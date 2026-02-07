import logging
from logging import LogRecord


class ColoredFormatter(logging.Formatter):
    def color_string(string, color):
        colors = {
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "white": "\033[97m",
            "yellow": "\033[93m",
            "red": "\033[91m",
        }
        ft = f"{colors[color]}\t{string}\033[0m\n"
        return ft

    def format(self, record: LogRecord) -> str:
        log_message = super().format(record)
        if record.levelname == "DEBUG":
            return self.color_string(log_message, "white")
        elif record.levelname == "WARNING":
            return self.color_string(log_message, "yellow")
        elif record.levelname == "ERROR":
            return self.color_string(log_message, "red")
        return log_message
