"""
Celery app tesztek - celery_app.py lefedettség növelése
"""

import pytest
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from celery.exceptions import Retry
from datetime import datetime, timedelta

# Hiányzó importok hozzáadása
from src.integrations.marketing.celery_app import (
    celery_app,
    detect_abandoned_carts,
    send_follow_up_email,
    send_follow_up_sms,
    cleanup_old_abandoned_carts,
    _detect_abandoned_carts_async,
    _send_follow_up_email_async,
    _send_follow_up_sms_async,
    _cleanup_old_abandoned_carts_async,
    start_celery_worker,
    start_celery_beat,
)
from src.integrations.marketing.abandoned_cart_detector import AbandonedCartDetector
from src.integrations.marketing.email_service import SendGridEmailService
from src.integrations.marketing.sms_service import TwilioSMSService


class TestCeleryAppConfiguration:
    """Celery app konfiguráció tesztek"""

    def test_celery_app_configuration(self):
        """Celery app konfiguráció teszt"""
        assert celery_app.main == "marketing_automation"

        # Konfiguráció ellenőrzések
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.task_track_started is True
        assert celery_app.conf.task_time_limit == 30 * 60
        assert celery_app.conf.task_soft_time_limit == 25 * 60
        assert celery_app.conf.worker_prefetch_multiplier == 1
        assert celery_app.conf.worker_max_tasks_per_child == 1000

    def test_celery_beat_schedule(self):
        """Celery beat ütemezés teszt"""
        schedule = celery_app.conf.beat_schedule

        assert "detect-abandoned-carts" in schedule
        assert "cleanup-old-carts" in schedule

        # detect-abandoned-carts konfiguráció
        detect_task = schedule["detect-abandoned-carts"]
        assert (
            detect_task["task"]
            == "src.integrations.marketing.celery_app.detect_abandoned_carts"
        )

        # cleanup-old-carts konfiguráció
        cleanup_task = schedule["cleanup-old-carts"]
        assert (
            cleanup_task["task"]
            == "src.integrations.marketing.celery_app.cleanup_old_abandoned_carts"
        )

    @patch.dict(os.environ, {"CELERY_BROKER_URL": "redis://test:6379/0"})
    def test_celery_environment_config(self):
        """Environment variable konfiguráció teszt"""
        # Új celery app létrehozása a teszteléshez
        from celery import Celery

        test_app = Celery("test_marketing_automation")
        test_app.conf.update(
            broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
            result_backend=os.getenv(
                "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
            ),
            timezone=os.getenv("CELERY_TIMEZONE", "Europe/Budapest"),
        )

        assert test_app.conf.broker_url == "redis://test:6379/0"
        assert test_app.conf.timezone == "Europe/Budapest"


class TestDetectAbandonedCartsTask:
    """Kosárelhagyás detektálás task tesztek"""

    @patch.dict(os.environ, {"TESTING": "true"})
    def test_detect_abandoned_carts_testing_env(self):
        """Teszt környezetben futtatás teszt"""
        result = detect_abandoned_carts.apply().result
        assert result == 0

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._detect_abandoned_carts_async")
    def test_detect_abandoned_carts_success(self, mock_async_func):
        """Sikeres detektálás teszt"""
        mock_async_func.return_value = 5

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            with patch("asyncio.set_event_loop") as mock_set_loop:
                # Valós event loop mock-olása
                mock_loop = Mock()
                mock_loop.run_until_complete.return_value = 5
                mock_loop_constructor.return_value = mock_loop

                result = detect_abandoned_carts.apply().result

                assert result == 5
                mock_loop.close.assert_called_once()

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._detect_abandoned_carts_async")
    def test_detect_abandoned_carts_exception_retry(self, mock_async_func):
        """Hiba esetén retry teszt"""
        mock_async_func.side_effect = Exception("Test error")

        with patch.object(detect_abandoned_carts, "retry") as mock_retry:
            detect_abandoned_carts.apply().result
            mock_retry.assert_called_once()

    @patch.dict(os.environ, {"TESTING": "true"})
    @patch("src.integrations.marketing.celery_app._detect_abandoned_carts_async")
    def test_detect_abandoned_carts_exception_testing_env(self, mock_async_func):
        """Teszt környezetben hiba esetén nem retry"""
        mock_async_func.side_effect = Exception("Test error")

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            mock_loop = Mock()
            mock_loop_constructor.return_value = mock_loop
            mock_loop.run_until_complete.side_effect = Exception("Test error")

            result = detect_abandoned_carts.apply().result

            assert result == 0  # Teszt környezetben 0-t ad vissza hiba esetén


class TestSendFollowUpEmailTask:
    """Email follow-up task tesztek"""

    @patch.dict(os.environ, {"TESTING": "true"})
    def test_send_follow_up_email_testing_env(self):
        """Teszt környezetben futtatás teszt"""
        result = send_follow_up_email.apply(args=["cart_123", 30]).result
        assert result is True

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._send_follow_up_email_async")
    def test_send_follow_up_email_success(self, mock_async_func):
        """Sikeres email küldés teszt"""
        mock_async_func.return_value = True

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            with patch("asyncio.set_event_loop") as mock_set_loop:
                mock_loop = Mock()
                mock_loop_constructor.return_value = mock_loop
                mock_loop.run_until_complete.return_value = True

                result = send_follow_up_email.apply(args=["cart_123", 30]).result

                assert result is True
                mock_loop.close.assert_called_once()

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._send_follow_up_email_async")
    def test_send_follow_up_email_exception_retry(self, mock_async_func):
        """Hiba esetén retry teszt"""
        mock_async_func.side_effect = Exception("Email error")

        with patch.object(send_follow_up_email, "retry") as mock_retry:
            send_follow_up_email.apply(args=["cart_123", 30]).result
            mock_retry.assert_called_once()




class TestSendFollowUpSMSTask:
    """SMS follow-up task tesztek"""

    @patch.dict(os.environ, {"TESTING": "true"})
    def test_send_follow_up_sms_testing_env(self):
        """Teszt környezetben futtatás teszt"""
        result = send_follow_up_sms.apply(args=["cart_123", 2]).result
        assert result is True

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._send_follow_up_sms_async")
    def test_send_follow_up_sms_success(self, mock_async_func):
        """Sikeres SMS küldés teszt"""
        mock_async_func.return_value = True

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            with patch("asyncio.set_event_loop") as mock_set_loop:
                mock_loop = Mock()
                mock_loop_constructor.return_value = mock_loop
                mock_loop.run_until_complete.return_value = True

                result = send_follow_up_sms.apply(args=["cart_123", 2]).result

                assert result is True
                mock_loop.close.assert_called_once()

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._send_follow_up_sms_async")
    def test_send_follow_up_sms_exception_retry(self, mock_async_func):
        """Hiba esetén retry teszt"""
        mock_async_func.side_effect = Exception("SMS error")

        with patch.object(send_follow_up_sms, "retry") as mock_retry:
            send_follow_up_sms.apply(args=["cart_123", 2]).result
            mock_retry.assert_called_once()




class TestCleanupOldAbandonedCartsTask:
    """Régi kosárok törlése task tesztek"""

    @patch.dict(os.environ, {"TESTING": "true"})
    def test_cleanup_old_abandoned_carts_testing_env(self):
        """Teszt környezetben futtatás teszt"""
        result = cleanup_old_abandoned_carts.apply().result
        assert result == 0

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._cleanup_old_abandoned_carts_async")
    def test_cleanup_old_abandoned_carts_success(self, mock_async_func):
        """Sikeres cleanup teszt"""
        mock_async_func.return_value = 10

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            with patch("asyncio.set_event_loop") as mock_set_loop:
                mock_loop = Mock()
                mock_loop_constructor.return_value = mock_loop
                mock_loop.run_until_complete.return_value = 10

                result = cleanup_old_abandoned_carts.apply().result

                assert result == 10
                mock_loop.close.assert_called_once()

    @patch.dict(os.environ, {"TESTING": "false"})
    @patch("src.integrations.marketing.celery_app._cleanup_old_abandoned_carts_async")
    def test_cleanup_old_abandoned_carts_exception(self, mock_async_func):
        """Hiba esetén False visszaadás teszt"""
        mock_async_func.side_effect = Exception("Cleanup error")

        with patch("asyncio.new_event_loop") as mock_loop_constructor:
            with patch("asyncio.set_event_loop") as mock_set_loop:
                mock_loop = Mock()
                mock_loop_constructor.return_value = mock_loop
                mock_loop.run_until_complete.side_effect = Exception("Cleanup error")

                result = cleanup_old_abandoned_carts.apply().result

                assert result is False


class TestAsyncHelperFunctions:
    """Async helper függvények tesztek"""

    @pytest.mark.asyncio
    @patch("src.integrations.marketing.abandoned_cart_detector.AbandonedCartDetector")
    async def test_detect_abandoned_carts_async(self, mock_detector_class):
        """_detect_abandoned_carts_async teszt"""
        mock_detector = AsyncMock()
        mock_detector.detect_abandoned_carts.return_value = 3
        mock_detector_class.return_value = mock_detector

        result = await _detect_abandoned_carts_async()

        assert result == 3
        mock_detector.detect_abandoned_carts.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.integrations.marketing.email_service.SendGridEmailService")
    @patch("src.integrations.marketing.abandoned_cart_detector.AbandonedCartDetector")
    async def test_send_follow_up_email_async(
        self, mock_detector_class, mock_email_service_class
    ):
        """_send_follow_up_email_async teszt"""
        mock_detector = AsyncMock()
        mock_email_service = AsyncMock()
        mock_detector.send_follow_up_email.return_value = True

        mock_detector_class.return_value = mock_detector
        mock_email_service_class.return_value = mock_email_service

        result = await _send_follow_up_email_async("cart_123", 30)

        assert result is True
        mock_detector.send_follow_up_email.assert_called_once_with(
            "cart_123", mock_email_service, 30
        )

    @pytest.mark.asyncio
    @patch("src.integrations.marketing.sms_service.TwilioSMSService")
    @patch("src.integrations.marketing.abandoned_cart_detector.AbandonedCartDetector")
    async def test_send_follow_up_sms_async(
        self, mock_detector_class, mock_sms_service_class
    ):
        """_send_follow_up_sms_async teszt"""
        mock_detector = AsyncMock()
        mock_sms_service = AsyncMock()
        mock_detector.send_follow_up_sms.return_value = True

        mock_detector_class.return_value = mock_detector
        mock_sms_service_class.return_value = mock_sms_service

        result = await _send_follow_up_sms_async("cart_123", 2)

        assert result is True
        mock_detector.send_follow_up_sms.assert_called_once_with(
            "cart_123", mock_sms_service, 2
        )

    @pytest.mark.asyncio
    @patch("src.integrations.marketing.abandoned_cart_detector.AbandonedCartDetector")
    async def test_cleanup_old_abandoned_carts_async(self, mock_detector_class):
        """_cleanup_old_abandoned_carts_async teszt"""
        mock_detector = AsyncMock()
        mock_detector.cleanup_old_abandoned_carts.return_value = 5
        mock_detector_class.return_value = mock_detector

        result = await _cleanup_old_abandoned_carts_async()

        assert result == 5
        mock_detector.cleanup_old_abandoned_carts.assert_called_once()


class TestCeleryWorkerHelpers:
    """Celery worker helper függvények tesztek"""

    @patch.object(celery_app, "worker_main")
    def test_start_celery_worker(self, mock_worker_main):
        """Celery worker indítás teszt"""
        start_celery_worker()

        mock_worker_main.assert_called_once_with(["worker", "--loglevel=info"])

    @patch.object(celery_app, "worker_main")
    def test_start_celery_beat(self, mock_worker_main):
        """Celery beat indítás teszt"""
        start_celery_beat()

        mock_worker_main.assert_called_once_with(["beat", "--loglevel=info"])


class TestTaskRegistration:
    """Task regisztráció tesztek"""

    def test_tasks_are_registered(self):
        """Task-ok regisztrálva vannak teszt"""
        registered_tasks = celery_app.tasks

        # Ellenőrizzük, hogy a task-ok regisztrálva vannak
        assert (
            "src.integrations.marketing.celery_app.detect_abandoned_carts"
            in registered_tasks
        )
        assert (
            "src.integrations.marketing.celery_app.send_follow_up_email"
            in registered_tasks
        )
        assert (
            "src.integrations.marketing.celery_app.send_follow_up_sms"
            in registered_tasks
        )
        assert (
            "src.integrations.marketing.celery_app.cleanup_old_abandoned_carts"
            in registered_tasks
        )

    def test_task_properties(self):
        """Task tulajdonságok teszt"""
        # detect_abandoned_carts task tulajdonságok
        detect_task = celery_app.tasks[
            "src.integrations.marketing.celery_app.detect_abandoned_carts"
        ]
        assert detect_task.max_retries == 3

        # send_follow_up_email task tulajdonságok
        email_task = celery_app.tasks[
            "src.integrations.marketing.celery_app.send_follow_up_email"
        ]
        assert email_task.max_retries == 3

        # send_follow_up_sms task tulajdonságok
        sms_task = celery_app.tasks[
            "src.integrations.marketing.celery_app.send_follow_up_sms"
        ]
        assert sms_task.max_retries == 3


class TestEdgeCases:
    """Edge case-ek tesztelése"""

    def test_missing_environment_variables(self):
        """Hiányzó environment variable-ok teszt"""
        with patch.dict(os.environ, {}, clear=True):
            # Default értékek ellenőrzése
            from celery import Celery

            test_app = Celery("test_app")
            test_app.conf.update(
                broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
                result_backend=os.getenv(
                    "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
                ),
                timezone=os.getenv("CELERY_TIMEZONE", "Europe/Budapest"),
            )

            assert test_app.conf.broker_url == "redis://localhost:6379/1"
            assert test_app.conf.result_backend == "redis://localhost:6379/1"
            assert test_app.conf.timezone == "Europe/Budapest"

    def test_task_with_different_delay_parameters(self):
        """Különböző delay paraméterekkel teszt"""
        # send_follow_up_email default delay_minutes=30
        with patch.dict(os.environ, {"TESTING": "true"}):
            result = send_follow_up_email.apply(args=["cart_123"]).result
            assert result is True

        # send_follow_up_sms default delay_hours=2
        with patch.dict(os.environ, {"TESTING": "true"}):
            result = send_follow_up_sms.apply(args=["cart_123"]).result
            assert result is True

    def test_async_loop_management(self):
        """Async loop kezelés teszt"""
        with patch.dict(os.environ, {"TESTING": "false"}):
            with patch(
                "src.integrations.marketing.celery_app._detect_abandoned_carts_async"
            ) as mock_async:
                mock_async.return_value = 2

                with patch("asyncio.new_event_loop") as mock_new_loop:
                    with patch("asyncio.set_event_loop") as mock_set_loop:
                        mock_loop = Mock()
                        mock_new_loop.return_value = mock_loop
                        mock_loop.run_until_complete.return_value = 2

                        result = detect_abandoned_carts.apply().result

                        assert result == 2
                        mock_new_loop.assert_called_once()
                        mock_set_loop.assert_called_once_with(mock_loop)
                        mock_loop.close.assert_called_once()
