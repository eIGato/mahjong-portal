import logging

import telegram
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.translation import activate
from telegram import ParseMode, Update
from telegram.error import BadRequest, ChatMigrated, NetworkError, TelegramError, TimedOut, Unauthorized
from telegram.ext import CallbackContext, CommandHandler, Defaults, Filters, MessageHandler, Updater

from online.handler import TournamentHandler
from online.models import TournamentGame, TournamentNotification
from tournament.models import Tournament
from utils.logs import set_up_logging

logger = logging.getLogger()
tournament_handler = TournamentHandler()


class Command(BaseCommand):
    def handle(self, *args, **options):
        set_up_logging(TournamentHandler.TELEGRAM_DESTINATION)
        bot = TelegramBot()
        bot.init()


class TelegramBot:
    def init(self):
        if not settings.TELEGRAM_ADMIN_USERNAME or not settings.TELEGRAM_ADMIN_USERNAME.startswith("@"):
            logger.error("Telegram admin username should starts with @")
            return

        required_configs = [
            settings.TOURNAMENT_ID,
            settings.TOURNAMENT_PUBLIC_LOBBY,
            settings.TOURNAMENT_PRIVATE_LOBBY,
            settings.TOURNAMENT_GAME_TYPE,
            settings.TELEGRAM_TOKEN,
            settings.TELEGRAM_CHANNEL_NAME,
        ]

        for config_item in required_configs:
            if not config_item:
                logger.error("One of the required tournament config wasn't configured.")
                return

        tournament = Tournament.objects.get(id=settings.TOURNAMENT_ID)
        tournament_handler.init(
            tournament,
            settings.TOURNAMENT_PRIVATE_LOBBY,
            settings.TOURNAMENT_GAME_TYPE,
            TournamentHandler.TELEGRAM_DESTINATION,
        )

        defaults = Defaults(parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        updater = Updater(token=settings.TELEGRAM_TOKEN, use_context=True, defaults=defaults)
        dispatcher = updater.dispatcher

        start_handler = CommandHandler("me", TelegramBot.set_tenhou_nickname)
        log_handler = CommandHandler("log", TelegramBot.set_game_log)
        status_handler = CommandHandler("status", TelegramBot.get_tournament_status)
        help_handler = CommandHandler("help", TelegramBot.help_bot)

        # background task
        updater.job_queue.run_repeating(TelegramBot.check_new_notifications, interval=3, first=0)

        dispatcher.add_handler(
            CommandHandler(
                "open_registration",
                TelegramBot.open_registration,
                filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "close_registration",
                TelegramBot.close_registration,
                filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME),
            )
        )

        dispatcher.add_handler(
            CommandHandler(
                "prepare_next_round",
                TelegramBot.prepare_next_round,
                filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "start_games", TelegramBot.start_games, filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME)
            )
        )

        dispatcher.add_handler(
            CommandHandler(
                "start_failed_games",
                TelegramBot.start_failed_games,
                filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME),
            )
        )

        dispatcher.add_handler(
            CommandHandler(
                "send_team_names_to_pantheon",
                TelegramBot.send_team_names_to_pantheon,
                filters=Filters.user(username=settings.TELEGRAM_ADMIN_USERNAME),
            )
        )

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(log_handler)
        dispatcher.add_handler(status_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_error_handler(TelegramBot.error_callback)
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, TelegramBot.new_tg_chat_member))

        logger.info("Starting the bot...")
        updater.start_polling()

        updater.idle()

    @staticmethod
    def open_registration(update: Update, context: CallbackContext):
        logger.info("Open confirmation stage")
        logger.info(f"Chat ID {update.message.chat_id}")
        tournament_handler.open_registration()
        context.bot.send_message(chat_id=update.message.chat_id, text="Ok")

    @staticmethod
    def check_new_notifications(context: telegram.ext.CallbackContext):
        notification = TournamentNotification.objects.filter(
            is_processed=False, destination=TournamentNotification.TELEGRAM, failed=False
        ).last()

        if not notification:
            return

        try:
            message = tournament_handler.get_notification_text("ru", notification)
            context.bot.send_message(chat_id=f"@{settings.TELEGRAM_CHANNEL_NAME}", text=message)

            notification.is_processed = True
            notification.save()

            logger.info(f"Notification id={notification.id} sent")
        except Exception as e:
            notification.failed = True
            notification.save()
            logger.error(e, exc_info=e)

    @staticmethod
    def set_game_log(update: Update, context: CallbackContext):
        logger.info("Set game log command. {}, {}".format(update.message.from_user.username, context.args))
        activate("ru")

        if not len(context.args):
            update.message.reply_text("Укажите ссылку на ханчан после команды.")
            return

        # it can take some time to add log, so lets show typing notification
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

        message, success = tournament_handler.add_game_log(context.args[0])
        update.message.reply_text(message)

    @staticmethod
    def get_tournament_status(update: Update, context: CallbackContext):
        logger.info("Get tournament status command")
        activate("ru")
        message = tournament_handler.get_tournament_status()
        context.bot.send_message(chat_id=update.message.chat_id, text=message)

    @staticmethod
    def help_bot(update: Update, context: CallbackContext):
        logger.info("Help")

        message = "1. Турнирное лобби:\n {} \n".format(tournament_handler.get_lobby_link())
        message += "2. Статистика:\n {} \n".format(tournament_handler.get_rating_link())
        message += "3. Текущие игры в лобби:\n https://tenhou.net/wg/?{} \n".format(
            settings.TOURNAMENT_PUBLIC_LOBBY[:5]
        )
        message += '4. Отправка лога игры через команду "/log http://tenhou.net..." \n'
        message += "5. Регламент турнира:\n https://mahjong.click/ru/online/ \n"
        message += (
            "6. Как получить ссылку на лог игры для flash/windows клиентов?\n https://imgur.com/gallery/7Hv52md \n"
        )
        message += (
            "7. Как получить ссылку на лог игры для мобильного/нового клиента?\n https://imgur.com/gallery/rP72mPx\n"
        )
        message += (
            "8. Как открыть турнирное лобби с мобильного/нового приложения?\n https://imgur.com/gallery/vcjsODf \n"
        )
        message += "9. Как открыть турнирное лобби с windows приложения?\n https://imgur.com/gallery/8vB307e"
        context.bot.send_message(chat_id=update.message.chat_id, text=message)

    @staticmethod
    def set_tenhou_nickname(update: Update, context: CallbackContext):
        activate("ru")
        logger.info("Nickname command. {}, {}".format(update.message.from_user.username, context.args))

        if not len(context.args):
            update.message.reply_text(text="Укажите ваш tenhou.net ник после команды.")
            return

        telegram_username = update.message.from_user.username
        if not telegram_username:
            text = (
                "Перед привязкой tenhou.net ника нужно установить username в настройках "
                "телеграма. Инструкция: http://telegramzy.ru/nik-v-telegramm/"
            )
            update.message.reply_text(text)
            return

        # it can take some time to validate nickname, so lets show typing notification
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

        tenhou_nickname = context.args[0]
        message = tournament_handler.confirm_participation_in_tournament(
            tenhou_nickname, telegram_username=telegram_username
        )
        update.message.reply_text(message)

    @staticmethod
    def new_tg_chat_member(update: Update, context: CallbackContext):
        # this happens when you add a bot to the chat
        # it raise an event with admin username
        username = update.message.from_user.username
        logger.info("New member. {}".format(username))
        if f"@{username}" == f"{settings.TELEGRAM_ADMIN_USERNAME}":
            return

        message = tournament_handler.new_tg_chat_member(username)
        update.message.reply_text(message)

    @staticmethod
    def prepare_next_round(update: Update, context: CallbackContext):
        logger.info("Prepare next round")

        message = tournament_handler.prepare_next_round()
        context.bot.send_message(chat_id=update.message.chat_id, text=message)

    @staticmethod
    def start_games(update: Update, context: CallbackContext):
        logger.info("Start games")

        games = TournamentGame.objects.filter(status=TournamentGame.NEW)
        context.bot.send_message(chat_id=update.message.chat_id, text="Запускаю игры...")

        for game in games:
            tournament_handler.start_game(game)

        context.bot.send_message(chat_id=update.message.chat_id, text="Ok")

    @staticmethod
    def start_failed_games(update: Update, context: CallbackContext):
        logger.info("Start failed games")

        games = TournamentGame.objects.filter(Q(status=TournamentGame.FAILED_TO_START) | Q(status=TournamentGame.NEW))
        context.bot.send_message(chat_id=update.message.chat_id, text="Запускаю игры...")

        for game in games:
            tournament_handler.start_game(game)

        context.bot.send_message(chat_id=update.message.chat_id, text="Ok")

    @staticmethod
    def close_registration(update: Update, context: CallbackContext):
        logger.info("Close registration")
        tournament_handler.close_registration()
        context.bot.send_message(chat_id=update.message.chat_id, text="Ok")

    @staticmethod
    def send_team_names_to_pantheon(update: Update, context: CallbackContext):
        logger.info("Send team names to pantheon")

        message = tournament_handler.send_team_names_to_pantheon()
        context.bot.send_message(chat_id=update.message.chat_id, text=message)

    @staticmethod
    def error_callback(update: Update, context: CallbackContext):
        logger.error(context.error)

        try:
            raise context.error
        except Unauthorized:
            # remove update.message.chat_id from conversation list
            pass
        except BadRequest:
            # handle malformed requests - read more below!
            pass
        except TimedOut:
            # handle slow connection problems
            pass
        except NetworkError:
            # handle other connection problems
            pass
        except ChatMigrated:
            # the chat_id of a group has changed, use e.new_chat_id instead
            pass
        except TelegramError:
            # handle all other telegram related errors
            pass
