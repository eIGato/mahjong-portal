from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone

from rating.calculation.inner import InnerRatingCalculation
from rating.mixins import RatingTestMixin
from rating.models import Rating, RatingDelta, RatingResult, TournamentCoefficients


class InnerRatingTestCase(TestCase, RatingTestMixin):

    def setUp(self):
        self.set_up_initial_objects()

    def test_tournament_coefficient_and_number_of_players(self):
        calculator = InnerRatingCalculation()

        tournament = self.create_tournament(players=20)
        self.assertEqual(calculator.players_coefficient(tournament), 0.5)

        tournament = self.create_tournament(players=40)
        self.assertEqual(calculator.players_coefficient(tournament), 1)

        tournament = self.create_tournament(players=80)
        self.assertEqual(calculator.players_coefficient(tournament), 2)

        tournament = self.create_tournament(players=92)
        self.assertEqual(calculator.players_coefficient(tournament), 2.15)

        tournament = self.create_tournament(players=120)
        self.assertEqual(calculator.players_coefficient(tournament), 2.5)

        tournament = self.create_tournament(players=150)
        self.assertEqual(calculator.players_coefficient(tournament), 2.5)

    def test_tournament_coefficient_and_number_of_sessions(self):
        calculator = InnerRatingCalculation()

        tournament = self.create_tournament(sessions=4)
        self.assertEqual(calculator.sessions_coefficient(tournament), 0.8)

        tournament = self.create_tournament(sessions=5)
        self.assertEqual(calculator.sessions_coefficient(tournament), 1)

        tournament = self.create_tournament(sessions=8)
        self.assertEqual(calculator.sessions_coefficient(tournament), 1.6)

        tournament = self.create_tournament(sessions=9)
        self.assertEqual(calculator.sessions_coefficient(tournament), 1.75)

        tournament = self.create_tournament(sessions=12)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.2)

        tournament = self.create_tournament(sessions=14)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.4)

        tournament = self.create_tournament(sessions=16)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.6)

        tournament = self.create_tournament(sessions=17)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.65)

        tournament = self.create_tournament(sessions=20)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.8)

        tournament = self.create_tournament(sessions=25)
        self.assertEqual(calculator.sessions_coefficient(tournament), 2.8)

    def test_calculate_player_base_rank(self):
        calculator = InnerRatingCalculation()
        tournament = self.create_tournament(players=80, sessions=4)

        result = self.create_tournament_result(tournament, place=1)
        self.assertEqual(calculator.calculate_base_rank(result), 1000)

        result = self.create_tournament_result(tournament, place=20)
        self.assertEqual(round(calculator.calculate_base_rank(result), 2), 759.49)

        result = self.create_tournament_result(tournament, place=40)
        self.assertEqual(round(calculator.calculate_base_rank(result), 2), 506.33)

        result = self.create_tournament_result(tournament, place=60)
        self.assertEqual(round(calculator.calculate_base_rank(result), 2), 253.16)

        result = self.create_tournament_result(tournament, place=80)
        self.assertEqual(calculator.calculate_base_rank(result), 0)

    def test_calculate_players_deltas(self):
        rating, _ = Rating.objects.get_or_create(type=Rating.INNER)

        first_player = self.create_player()
        second_player = self.create_player()

        calculator = InnerRatingCalculation()

        # First tournament

        tournament = self.create_tournament(players=4, sessions=2)
        self.create_tournament_result(tournament, place=1, player=first_player)
        self.create_tournament_result(tournament, place=2, player=second_player)

        calculator.calculate_players_deltas(tournament, rating)

        # Second tournament

        tournament = self.create_tournament(players=4, sessions=2)
        self.create_tournament_result(tournament, place=4, player=first_player)
        self.create_tournament_result(tournament, place=1, player=second_player)

        calculator.calculate_players_deltas(tournament, rating)

        rating_deltas = RatingDelta.objects.filter(player=first_player).order_by('id')

        self.assertEqual(rating_deltas.count(), 2)
        self.assertEqual(rating_deltas[0].delta, 500)
        self.assertEqual(rating_deltas[0].base_rank, 1000)

        self.assertEqual(rating_deltas[1].delta, 0)
        self.assertEqual(rating_deltas[1].base_rank, 0)

        rating_deltas = RatingDelta.objects.filter(player=second_player).order_by('id')

        self.assertEqual(rating_deltas.count(), 2)
        self.assertEqual(float(rating_deltas[0].delta), 333.33)
        self.assertEqual(float(rating_deltas[0].base_rank), 666.67)

        self.assertEqual(float(rating_deltas[1].delta), 500)
        self.assertEqual(rating_deltas[1].base_rank, 1000)

    def test_calculate_players_delta_and_tournament_age(self):
        rating, _ = Rating.objects.get_or_create(type=Rating.INNER)
        first_player = self.create_player()
        calculator = InnerRatingCalculation()

        tournament = self.create_tournament(players=4, sessions=2)
        self.create_tournament_result(tournament, place=1, player=first_player)

        calculator.calculate_players_deltas(tournament, rating)

        rating_delta = RatingDelta.objects.filter(player=first_player).first()
        self.assertEqual(rating_delta.delta, 500)
        self.assertEqual(rating_delta.base_rank, 1000)

        RatingDelta.objects.all().delete()
        tournament.end_date = timezone.now().date() - timedelta(days=400)
        tournament.save()
        calculator.calculate_players_deltas(tournament, rating)

        rating_delta = RatingDelta.objects.filter(player=first_player).first()
        self.assertEqual(rating_delta.delta, 330)
        self.assertEqual(rating_delta.base_rank, 1000)

        RatingDelta.objects.all().delete()
        tournament.end_date = timezone.now().date() - timedelta(days=600)
        tournament.save()
        calculator.calculate_players_deltas(tournament, rating)

        rating_delta = RatingDelta.objects.filter(player=first_player).first()
        self.assertEqual(rating_delta.delta, 165)
        self.assertEqual(rating_delta.base_rank, 1000)

    def test_calculate_count_of_sessions_for_ema_tournaments(self):
        calculator = InnerRatingCalculation()

        start_date = datetime(year=2017, month=10, day=1)
        end_date = datetime(year=2017, month=10, day=2)
        tournament = self.create_tournament(players=80, sessions=0, start_date=start_date, end_date=end_date)

        self.assertEqual(calculator._assume_number_of_sessions(tournament), 4)

        start_date = datetime(year=2017, month=9, day=25)
        end_date = datetime(year=2017, month=9, day=27)
        tournament = self.create_tournament(players=80, sessions=0, start_date=start_date, end_date=end_date)

        self.assertEqual(calculator._assume_number_of_sessions(tournament), 8)

        start_date = datetime(year=2017, month=9, day=25)
        end_date = datetime(year=2017, month=9, day=28)
        tournament = self.create_tournament(players=80, sessions=0, start_date=start_date, end_date=end_date)

        self.assertEqual(calculator._assume_number_of_sessions(tournament), 12)

    def test_calculate_number_of_accepted_tournaments(self):
        calculator = InnerRatingCalculation()

        self.assertEqual(calculator._determine_tournaments_number(5), 5)
        self.assertEqual(calculator._determine_tournaments_number(6), 6)
        self.assertEqual(calculator._determine_tournaments_number(7), 7)
        self.assertEqual(calculator._determine_tournaments_number(8), 8)
        self.assertEqual(calculator._determine_tournaments_number(9), 9)
        self.assertEqual(calculator._determine_tournaments_number(10), 9)
        self.assertEqual(calculator._determine_tournaments_number(15), 13)
        self.assertEqual(calculator._determine_tournaments_number(20), 17)
        self.assertEqual(calculator._determine_tournaments_number(25), 21)

    def test_calculate_age_weight_of_tournament(self):
        calculator = InnerRatingCalculation()

        now = timezone.now().date()

        tournament = self.create_tournament(end_date=now)
        self.assertEqual(calculator.tournament_age(tournament), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=60))
        self.assertEqual(calculator.tournament_age(tournament), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=365))
        self.assertEqual(calculator.tournament_age(tournament), 100)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 + 31))
        self.assertEqual(calculator.tournament_age(tournament), 66)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 + 7 * 31))
        self.assertEqual(calculator.tournament_age(tournament), 33)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2))
        self.assertEqual(calculator.tournament_age(tournament), 33)

        tournament = self.create_tournament(end_date=now - timedelta(days=365 * 2 + 2))
        self.assertEqual(calculator.tournament_age(tournament), 0)

    def test_calculate_players_rating_rank(self):
        rating, _ = Rating.objects.get_or_create(type=Rating.INNER)

        tournament = self.create_tournament(
            end_date=timezone.now().date() - timedelta(days=100)
        )

        calculator = InnerRatingCalculation()

        deltas = [500, 600, 100, 200, 400, 900, 1000, 800, 900, 100]
        for delta in deltas:
            self.create_rating_delta(rating, tournament, self.player, delta)

        TournamentCoefficients.objects.create(rating=rating, tournament=tournament, coefficient=2, age=100)
        calculator.calculate_players_rating_rank(rating)

        delta_object = RatingResult.objects.get(player=self.player, rating=rating)

        self.assertEqual(float(delta_object.score), 375)
        self.assertEqual(delta_object.place, 1)

    def test_calculate_players_rating_rank_and_not_enough_tournaments(self):
        rating, _ = Rating.objects.get_or_create(type=Rating.INNER)

        tournament = self.create_tournament(end_date=timezone.now().date() - timedelta(days=100))

        calculator = InnerRatingCalculation()

        deltas = [1000, 1000]
        for delta in deltas:
            self.create_rating_delta(rating, tournament, self.player, delta)

        TournamentCoefficients.objects.create(rating=rating, tournament=tournament, coefficient=2, age=100)
        calculator.calculate_players_rating_rank(rating)

        delta_object = RatingResult.objects.get(player=self.player, rating=rating)

        self.assertEqual(float(delta_object.score), 267.86)