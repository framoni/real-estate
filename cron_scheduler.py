from crontab import CronTab


def schedule():
    cron = CronTab(user="francescoramoni")
    job = cron.new(command="python scraper_immobiliare.py")
    job.day.every(1)
    cron.write()


if __name__ == "__main__":
    schedule()