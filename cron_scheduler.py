from crontab import CronTab


def schedule():
    cron = CronTab(user="francescoramoni")
    job = cron.new(command="export PATH=$PATH:/usr/local/bin; source /opt/anaconda3/bin/activate real-estate; python3 ~/Projects/real-estate/immobiliare.py", comment="imm_scraper")
    job.day.every(1)
    cron.write()


def remove():
    cron = CronTab(user="francescoramoni")
    for job in cron:
        if job.comment == 'imm_scraper':
            cron.remove(job)
    cron.write()


if __name__ == "__main__":
    remove()
    # schedule()
