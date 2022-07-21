import streamlit as st
import ssl
import json
import pandas as pd
import datetime
from six.moves.urllib import request
from dateutil.relativedelta import relativedelta

ssl._create_default_https_context = ssl._create_unverified_context

st.markdown("# Extract date from Goooooooogle 🎈")

st.text_input("Domain or URL", key="url", value="https://semji.com")

col1, col2 = st.columns(2)

col1.date_input(
    "From",
    datetime.date(2020, 1, 1),
    key="date_from"
)

col2.date_input(
    "To",
    datetime.date.today(),
    key="date_to"
)


@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')

def get_relative_date_from_organic_result(str_days_ago):
    TODAY = datetime.date.today()
    splitted = str_days_ago.split()

    if len(splitted) == 1 and splitted[0].lower() == 'today':
        return TODAY
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        return TODAY - relativedelta(days=1)
    elif splitted[1].lower() in ['minute', 'minutes', 'min', 'mins']:
        return datetime.datetime.now() - relativedelta(minutes=int(splitted[0]))
    elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        return datetime.datetime.now() - relativedelta(hours=int(splitted[0]))
    elif splitted[1].lower() in ['day', 'days', 'd']:
        return TODAY - relativedelta(days=int(splitted[0]))
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        return TODAY - relativedelta(weeks=int(splitted[0]))
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        return TODAY - relativedelta(months=int(splitted[0]))
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        return TODAY - relativedelta(years=int(splitted[0]))
    else:
        return None

@st.cache
def scrape_google(query, start):
    opener = request.build_opener(
        request.ProxyHandler({
            'http':  f"http://{st.secrets.brightdata.username}:{st.secrets.brightdata.password}@zproxy.lum-superproxy.io:22225",
            'https': f"http://{st.secrets.brightdata.username}:{st.secrets.brightdata.password}@zproxy.lum-superproxy.io:22225"
        })
    )

    data = opener.open(f"{query}&start={start}&lum_json=1").read()

    return data

def extract_results(data):
    rows = []

    if 'organic' in data:

        for result in data['organic']:
            link = result['link'] if 'link' in result else ''
            title = result['title'] if 'title' in result else ''

            if not 'extensions' in result:
                result['extensions'] = []

            date = None
            for extension in result['extensions']:
                try:
                    date = datetime.datetime.strptime(extension['text'], "%b %d, %Y")
                except:
                    date = get_relative_date_from_organic_result(extension['text'])
                finally:
                    if date is not None:
                        break;

            rows.append({
                'date': date.strftime("%Y-%m-%d") if date else '',
                'link': link,
                'title': title
            })

    return rows

if st.button('Start Google scraping'):
    start = 0
    rows = []
    google_query = f"https://www.google.com/search?q=site:{st.session_state.url}&num=100&tbs=cdr:1,cd_min:{st.session_state.date_from.strftime('%d/%m/%Y')},cd_max:{st.session_state.date_to.strftime('%d/%m/%Y')}&tbm="

    st.markdown(f"[Generated Google query]({google_query})")

    results_count = None
    while True:
        data = json.loads(scrape_google(google_query, start))
        rows += extract_results(data)
        if results_count == None:
            results_count = data['general']['results_cnt']

        start = start + 100
        if not 'pagination' in data or not 'next_page_link' in data['pagination']:
            break

    dataframe = pd.DataFrame(rows)

    st.markdown("## Results")
    st.markdown(f"Total results: {results_count}")

    st.dataframe(dataframe)

    csv = convert_df(dataframe)

    st.download_button(
       "Download as CSV",
       csv,
       "serp_results.csv",
       "text/csv",
       key='download-csv'
    )
