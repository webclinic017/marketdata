#**********************************************************
#* CATEGORY	SOFTWARE
#* GROUP	MARKET DATA
#* AUTHOR	LANCE HAYNIE <LANCE@HAYNIEMAIL.COM>
#* FILE		NEWS.PY
#**********************************************************
#ETL Stock Market Data
#Copyright 2020 Haynie IPHC, LLC
#Developed by Haynie Research & Development, LLC
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.#
#You may obtain a copy of the License at
#http://www.apache.org/licenses/LICENSE-2.0
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
import sys
import urllib.request as urlreq
import json
import pandas as pd
import logging
from datetime import date
from .settings import settings_data
from .database import db,dw
from .functions import numtest

logging.basicConfig(format='%(levelname)s - %(message)s', level=settings_data['global']['loglevel'])

api_base = settings_data['datasources']['IEX']['url']
api_key = settings_data['datasources']['IEX']['key']

def news(uuid,symbol):
    logging.debug("Processing news data for: " + symbol + ".")

    cursor = db.cursor()
    try:
        api = f"{api_base}/stock/{symbol}/news/last/50?token={api_key}"
        response_data = json.loads(urlreq.urlopen(api).read().decode())

        datetime    = response_data[0]['datetime']
        headline    = response_data[0]['headline']
        source      = response_data[0]['source']
        url         = response_data[0]['url']
        summary     = response_data[0]['summary']
        related     = response_data[0]['related']
        image       = response_data[0]['image']
        lang        = response_data[0]['lang']
        paywall     = response_data[0]['hasPaywall']
        current_dt  = date.today()

        try:
            sql = f"""
            INSERT INTO
            daily(
                security_id,
                datetime,
                headline,
                source,
                url,
                summary,
                import_date)
            values(
                {uuid},
                {datetime},
                {headline},
                {source},
                {url},
                {summary},
                '{current_dt}');
            """

            try:
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                error = format(str(e))
                if error.find("Duplicate entry") != -1:
                    logging.debug("Data already exists for " + symbol + " on datetime " + datetime + ".")
                else:
                    logging.error(format(str(e)))

        except Exception as e:
            logging.error(format(str(e)))

    except Exception as e:
        logging.error(format(str(e)))

def update():
    dw_cursor = dw.cursor()

    try:
        dw_cursor.execute("select uuid, symbol from security")
        results = dw_cursor.fetchall()
        for row in results:
            uuid = row[0]
            symbol = row[1]
            news(uuid, symbol)

    except Exception as e:
        logging.error(format(str(e)))
        sys.exit(1)
    dw.close()
