import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from time import strftime
from typing import List
from time import sleep

AUTH_TOKEN = 0###########################


class DOTScraper:
    """
    Scrapes parameters by DOT number and updates records in Zoho CRM
    """

    @staticmethod
    def get_leads(start: int) -> list:
        url = ("https://crm.zoho.com/crm/private/json/Leads/getRecords?"
               "authtoken=%s&scope=crmapi&newFormat=2&fromIndex=%i&toIndex=%i" % (AUTH_TOKEN, start, start + 199))
        response = requests.get(url)
        return [row['FL'] for row in response.json()['response']['result']['Leads']['row']]

    @staticmethod
    def scrap_dot(dot: int) -> dict:
        def get():
            try:
                return requests.get("https://ai.fmcsa.dot.gov/SMS/Carrier/%i/CompleteProfile.aspx" % dot).text
            except ConnectionError:
                get()
        response = get()

        bs = BeautifulSoup(response, "lxml")
        try:
            result = {'SAFETY RATING': bs.find("div", {"id": "Rating"}).text}
        except AttributeError:
            return 0
        iter_tuple = (("UNSAFE DRIVING", 0), ("HOS COMPLIANCE", 2), ("VEHICLE MAINTENANCE", 3), ("DRUG ALCOHOL", 4),
                      ("DRIVER FITNESS", 6))
        for key, val in iter_tuple:
            try:
                result[key] = bs.find("tr", {"class": "valueRow sumData"}).find_all("td")[val].span.text
            except AttributeError:
                result[key] = "Not Avaliable"

        try:
            result["Total Fleet Size"] = bs.find("div", {"id": "basicInfo"}).find_all("ul")[1].find_all("li")[1].text[50:].strip()
        except AttributeError:
            pass
        result["LAST RATING UPDATE"] = strftime('%m/%d/%Y %I:%M %p')
        return result

    @staticmethod
    def update(leads: list):
        def encode(normal: list) -> str:
            encoded = "<Leads>"
            i = 1
            for entry in normal:
                encoded += '<row no="%i">' % i
                for key in entry:
                    encoded += '<FL val="%s">%s</FL>' % (key, entry[key])
                encoded += "</row>"
                i += 1
            encoded += "</Leads>"
            return encoded

        url = "https://crm.zoho.com/crm/private/xml/Leads/updateRecords"
        data = {"authtoken": AUTH_TOKEN, "scope": "crmapi", "version": 4, "xmlData": encode(leads)}
        print(requests.post(url, data).text)

    def __init__(self):
        def decode(weird: List[dict]) -> dict:
            normal = {}
            for d in weird:
                normal[d['val']] = d['content']
            return normal

        i = 1
        while True:
            leads = self.get_leads(i)
            leads_to_update = []
            i += 200
            if len(leads) != 200:
                i = 1
            for lead in leads:
                lead_decoded = decode(lead)
                if lead_decoded["DOT Number"] == 'null':
                    continue
                else:
                    new = self.scrap_dot(int(lead_decoded["DOT Number"]))
                    if not new:
                        new = {"UNSAFE DRIVING": "Incorrect DOT Number"}
                        leads_to_update.append(new)
                        continue
                new["Id"] = lead_decoded["LEADID"]
                new["LEADID"] = lead_decoded["LEADID"]

                if lead_decoded["UNSAFE 3 MONTH CHANGE"] != 'null':
                    value_6_months_ago = 100 * float(lead_decoded["UNSAFE DRIVING"]) / 100 + float(
                        lead_decoded["UNSAFE 3 MONTH CHANGE"])
                    try:
                        new["UNSAFE 6 MONTH CHANGE"] = (value_6_months_ago - float(new["UNSAFE DRIVING"])) / (
                            0 - value_6_months_ago)
                    except ZeroDivisionError:
                        if value_6_months_ago == float(new["UNSAFE DRIVING"]):
                            new["UNSAFE 6 MONTH CHANGE"] = 0
                        else:
                            new["UNSAFE 6 MONTH CHANGE"] = 100

                if lead_decoded["UNSAFE DRIVING"] != 'null':
                    value_3_months_ago = float(lead_decoded["UNSAFE DRIVING"])
                    try:
                        new["UNSAFE 3 MONTH CHANGE"] = (value_3_months_ago - float(new["UNSAFE DRIVING"])) / (
                            0 - value_3_months_ago)
                    except ZeroDivisionError:
                        if value_3_months_ago == float(new["UNSAFE DRIVING"]):
                            new["UNSAFE 3 MONTH CHANGE"] = 0
                        else:
                            new["UNSAFE 3 MONTH CHANGE"] = 100

                if lead_decoded["MAINTENANCE 3 MONTH CHANGE"] != 'null':
                    value_6_months_ago = 100 * float(lead_decoded["VEHICLE MAINTENANCE"]) / 100 + float(
                        lead_decoded["MAINTENANCE 3 MONTH CHANGE"])
                    try:
                        new["MAINTENANCE 6 MONTH CHANGE"] = (value_6_months_ago - float(new["VEHICLE MAINTENANCE"])) / (
                            0 - value_6_months_ago)
                    except ZeroDivisionError:
                        if value_6_months_ago == float(new["VEHICLE MAINTENANCE"]):
                            new["MAINTENANCE 6 MONTH CHANGE"] = 0
                        else:
                            new["MAINTENANCE 6 MONTH CHANGE"] = 100

                if lead_decoded["VEHICLE MAINTENANCE"] != 'null':
                    value_3_months_ago = float(lead_decoded["VEHICLE MAINTENANCE"])
                    try:
                        new["MAINTENANCE 3 MONTH CHANGE"] = (value_3_months_ago - float(new["VEHICLE MAINTENANCE"])) / (
                            0 - value_3_months_ago)
                    except ZeroDivisionError:
                        if value_3_months_ago == float(new["VEHICLE MAINTENANCE"]):
                            new["MAINTENANCE 3 MONTH CHANGE"] = 0
                        else:
                            new["MAINTENANCE 3 MONTH CHANGE"] = 100

                if lead_decoded["HOS 3 MONTH CHANGE"] != 'null':
                    value_6_months_ago = 100 * float(lead_decoded["HOS COMPLIANCE"]) / 100 + float(
                        lead_decoded["HOS 3 MONTH CHANGE"])
                    try:
                        new["HOS 6 MONTH CHANGE"] = (value_6_months_ago - float(new["HOS COMPLIANCE"])) / (
                            0 - value_6_months_ago)
                    except ZeroDivisionError:
                        if value_6_months_ago == float(new["HOS COMPLIANCE"]):
                            new["HOS 6 MONTH CHANGE"] = 0
                        else:
                            new["HOS 6 MONTH CHANGE"] = 100

                if lead_decoded["HOS COMPLIANCE"] != 'null':
                    value_3_months_ago = float(lead_decoded["HOS COMPLIANCE"])
                    try:
                        new["HOS 3 MONTH CHANGE"] = (value_3_months_ago - float(new["HOS COMPLIANCE"])) / (
                            0 - value_3_months_ago)
                    except ZeroDivisionError:
                        if value_3_months_ago == float(new["HOS COMPLIANCE"]):
                            new["HOS 3 MONTH CHANGE"] = 0
                        else:
                            new["HOS 3 MONTH CHANGE"] = 100

                leads_to_update.append(new)
                if len(leads_to_update) == 100:
                    self.update(leads_to_update)
                    leads_to_update = []
                sleep(3)
            self.update(leads_to_update)

DOTScraper()
