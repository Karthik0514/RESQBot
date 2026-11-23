"""Launch RESQBOT V7."""
from resqbot.services.logging_service import configure_logging
from resqbot.ui.app import App

if __name__ == "__main__":
    logger = configure_logging()
    logger.info("RESQBOT V7 starting")
    App().run()
    logger.info("RESQBOT V7 stopped")
