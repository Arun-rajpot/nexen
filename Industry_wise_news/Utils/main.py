from Scripts import Acuite,brickwork,care,cricil,icra,infomerics,india_ratings
import schedule
import time

def main():

    Acuite.Acuite_main()
    brickwork.brikcwork_main()
    care.care_main()
    cricil.crisil_main()
    icra.icra_main()
    infomerics.infomerics_main()
    india_ratings.industry_news_indiarating()

main()
# # Schedule the job
# schedule.every().day.at("17:24").do(main)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)