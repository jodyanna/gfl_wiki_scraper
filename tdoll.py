"""This app scrapes tdoll stats, profile images from GFL Wiki"""

from bs4 import BeautifulSoup
import requests
import shutil
import time
import csv
import json
import os

# Global Constants
CRAWL_DELAY = 20


def main():
    print("Now scraping...")
    init_save_files(["saves/tdoll_data.json", "saves/tdoll_data.csv"])
    names = get_tdoll_names("https://en.gfwiki.com/wiki/T-Doll_Index")
    scrape_n_save(names)
    clean_up("saves/tdoll_data.json")


def scrape_n_save(names):
    """Get and parse html data into dictionary then write to file for each entry in 'names' list."""
    for i in range(len(names)):
        print(names[i])
        tdoll_url = "https://en.gfwiki.com/wiki/" + names[i].replace(" ", "_")
        soup = get_html(tdoll_url)

        try:
            tdoll_data = {"id": get_id(soup), "name": names[i].replace(" ", "_"), "wclass": get_wclass(soup),
                          "rarity": get_rarity(soup), "hp": get_hp(soup), "ammo_cost": get_ammo_cost(soup),
                          "ration_cost": get_ration_cost(soup), "damage": get_damage(soup),
                          "evasion": get_evasion(soup), "accuracy": get_accuracy(soup), "rof": get_rof(soup),
                          "move_speed": get_move_speed(soup), "crit_rate": get_crit_rate(soup),
                          "crit_damage": get_crit_damage(soup), "armor_pen": get_armor_pen(soup),
                          "aura_tiles": get_aura_tiles(soup), "aura_targets": get_aura_targets(soup),
                          "aura_buffs": get_aura_buffs(soup)}
            tdoll_data["armor"] = get_armor(tdoll_data["wclass"], soup)
            tdoll_data["mag_size"] = get_mag_size(tdoll_data["wclass"], soup)
            tdoll_data["aura_buff_vals"] = get_aura_buff_vals(tdoll_data["wclass"], soup)

            write_json(tdoll_data, "tdoll_data")
            write_csv(tdoll_data, "tdoll_data")

            get_prof_img(tdoll_data["name"], soup)

        except Exception as err:
            print("Error:" + str(err) + ", Aborted scraping " + names[i])


def get_tdoll_names(url):
    """Collect and return tdoll names from url as list of strings."""
    soup = get_html(url)
    spans = soup.find_all("span", class_="name")

    return [span.text for span in spans]


def get_html(url):
    """Request then return html data of url."""
    try:
        source = requests.get(url)
        soup = BeautifulSoup(source.content, "html.parser")
        del source
        time.sleep(CRAWL_DELAY)

        return soup

    except requests.exceptions as err:
        print(err)


def get_id(soup):
    """Parse and return tdoll id from html as string."""
    return soup.find("span", class_="indexnumber").text


def get_wclass(soup):
    """Parse and return tdoll weapon class from html as string."""
    return soup.find("img", class_="classificationsymbol").get("src").split("_")[1]


def get_rarity(soup):
    """Parse and return tdoll rarity level from html as string."""
    return soup.find("img", class_="classificationsymbol").get("src")[-9:-4]


def get_hp(soup):
    """Parse and return tdoll hp data as list of ints."""
    min_hp = int(soup.find("span", attrs={"data-tdoll-stat-id": "min_hp"}).text)
    max_hp = int(soup.find("span", attrs={"data-tdoll-stat-id": "max_hp"}).text)
    max_hp_wd = int(soup.find("span", attrs={"data-tdoll-stat-id": "hpmaxwd"}).text)

    return [min_hp, max_hp, max_hp_wd]


def get_ammo_cost(soup):
    """Parse and return tdoll ammo cost data as list of ints."""
    div = soup.find("div", class_="stattabcontainer")
    ammo_costs = div.find_all("td")[4].text.split(" / ")
    for i, cost in enumerate(ammo_costs):
        ammo_costs[i] = int(cost.strip("\n")[0:-4])

    return ammo_costs


def get_ration_cost(soup):
    """Parse and return tdoll ration cost data as list of ints."""
    div = soup.find("div", class_="stattabcontainer")
    ration_costs = div.find_all("td")[5].text.split(" / ")
    for i, cost in enumerate(ration_costs):
        ration_costs[i] = int(cost.strip("\n")[0:-4])

    return ration_costs


def get_damage(soup):
    """Parse and return tdoll damage stat data as list of ints."""
    min_dmg = int(soup.find("td", attrs={"data-tdoll-stat-id": "min_dmg"}).text)
    max_dmg = int(soup.find("td", attrs={"data-tdoll-stat-id": "max_dmg"}).text)

    return [min_dmg, max_dmg]


def get_evasion(soup):
    """Parse and return tdoll evasion stat data as list of ints."""
    min_eva = int(soup.find("td", attrs={"data-tdoll-stat-id": "min_eva"}).text)
    max_eva = int(soup.find("td", attrs={"data-tdoll-stat-id": "max_eva"}).text)

    return [min_eva, max_eva]


def get_accuracy(soup):
    """Parse and return tdoll accuracy stat data as list of ints."""
    min_acc = int(soup.find("td", attrs={"data-tdoll-stat-id": "min_acc"}).text)
    max_acc = int(soup.find("td", attrs={"data-tdoll-stat-id": "max_acc"}).text)

    return [min_acc, max_acc]


def get_rof(soup):
    """Parse and return tdoll rate of fire stat data as list of ints."""
    min_rof = int(soup.find("td", attrs={"data-tdoll-stat-id": "min_rof"}).text)
    max_rof = int(soup.find("td", attrs={"data-tdoll-stat-id": "max_rof"}).text)

    return [min_rof, max_rof]


def get_move_speed(soup):
    """Parse and return tdoll movement speed stat as int."""
    return int(soup.find("td", attrs={"data-tdoll-stat-id": "mov"}).text)


def get_armor(wclass, soup):
    """Parse and return tdoll armor stat data as list of ints or int 0."""
    if wclass == "SG":
        min_armor = int(soup.find("td", attrs={"data-tdoll-stat-id": "min_armor"}).text)
        max_armor = int(soup.find("td", attrs={"data-tdoll-stat-id": "max_armor"}).text)

        return [min_armor, max_armor]
    else:
        return 0


def get_crit_rate(soup):
    """Parse and return tdoll critical rate percent as floating decimal."""
    return convert_percent(soup.find("td", attrs={"data-tdoll-stat-id": "crit"}).text.strip("\n"))


def get_crit_damage(soup):
    """Parse and return tdoll critical damage increase percent as floating decimal."""
    return convert_percent(soup.find("td", attrs={"data-tdoll-stat-id": "critdmg"}).text.strip("\n"))


def get_armor_pen(soup):
    """Parse and return tdoll armor penetration stat as int."""
    return int(soup.find("td", attrs={"data-tdoll-stat-id": "penetration"}).text)


def get_mag_size(wclass, soup):
    """Parse and return tdoll magazine size stat as int, or as None/null."""
    if wclass == "SG" or wclass == "MG":
        return int(soup.find("td", attrs={"data-tdoll-stat-id": "clipsize"}).text)
    else:
        return None


def get_aura_tiles(soup):
    """Parse and return tdoll aura tile data as list containing strings or None/null values."""
    tile_grid_table = soup.find("table", class_="tilegridtable")
    aura_tiles = [td.get("class") for td in tile_grid_table.find_all("td")]

    for i, tile in enumerate(aura_tiles):
        if tile is not None:
            aura_tiles[i] = tile[0]

    return aura_tiles


def get_aura_targets(soup):
    """Determine and return which weapon classes are effected by tdoll aura as list of strings."""
    div = soup.find("div", attrs={"data-tdoll-stat-id": "aura1"}).text.split(" ")
    rf_check = True
    mg_check = True
    targets = []

    for string in div:
        if "all" == string.lower():
            for wclass in ["hg", "smg", "ar", "sg", "mg", "rf"]:
                targets.append(wclass)
        if "submachine" == string.lower() or "sub" in string.lower() or "SMG" in string:
            targets.append("smg")
            mg_check = False
        if "assault" == string.lower() or "AR" in string:
            targets.append("ar")
            rf_check = False
        if "handguns" == string.lower() or "pistols" == string or "HG" in string:
            targets.append("hg")
        if "shotguns" == string.lower() or "SG" in string:
            targets.append("sg")
        if "machine" == string.lower() and mg_check or "machineguns" == string.lower() and mg_check or "MG" == string \
                or "MGs" == string:
            targets.append("mg")
        if "rifles" == string.lower() and rf_check or "RF" in string and rf_check:
            targets.append("rf")

    return targets


def get_aura_buffs(soup):
    """Determine and return which stats are effected by tdoll aura as list of strings."""
    div1 = soup.find("div", attrs={"data-tdoll-stat-id": "aura2"}).text
    div2 = soup.find("div", attrs={"data-tdoll-stat-id": "aura3"}).text
    buffs = []

    for div in [div1, div2]:
        for string in div.split(" "):
            if string.lower() == "damage" or string.lower() == "firepower":
                buffs.append("damage")
            if string.lower() == "fire":
                buffs.append("rof")
            if string.lower() == "accuracy":
                buffs.append("accuracy")
            if string.lower() == "evasion":
                buffs.append("evasion")
            if string.lower() == "critical":
                buffs.append("crit_rate")
            if string.lower() == "skill":
                buffs.append("skill_cd")
            if string.lower() == "armor" or string.lower() == "armour":
                buffs.append("armor")

    return buffs


def get_aura_buff_vals(wclass, soup):
    """Parse and return tdoll aura stat percent increase data as list of floats, or list of lists containing floats."""
    div1 = soup.find("div", attrs={"data-tdoll-stat-id": "aura2"})
    div2 = soup.find("div", attrs={"data-tdoll-stat-id": "aura3"})
    vals = []

    for div in [div1, div2]:
        if wclass == "HG":
            try:
                hg_vals = [convert_percent(string[:-5]) for string in div.div.text.split("/") if "%" in string]
                vals.append(hg_vals)
            except AttributeError:
                pass
        else:
            for string in div.text.split(" "):
                if "%" in string:
                    vals.append(convert_percent(string))

    return vals


def get_prof_img(name, soup):
    """Parse tdoll profile img url from html then request download image as .png"""
    img_url = soup.find("img", class_="dollprofileimage").get("src")

    # create filename
    if "/" in name:
        name = name.replace("/", "")
    filename = "images/" + name + "_profile.png"

    # make request and save image
    response = requests.get(img_url, stream=True)
    with open(filename, 'wb') as outfile:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, outfile)
    del response
    time.sleep(CRAWL_DELAY)


def convert_percent(string):
    """Convert numerical percent strings into floating decimals"""
    string = string.rstrip("%")
    percent = float(string) / 100

    return percent


def write_json(data, file_name):
    """Save data stored in dictionary into .json file"""
    file_name = "saves/" + file_name + ".json"

    with open(file_name, "a", encoding='utf-8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=4)
        outfile.write(",\n")


def write_csv(data, file_name):
    """Save data stored in dictionary into .csv file"""
    file_name = "saves/" + file_name + ".csv"
    headers = [k for k, _ in data.items()]

    with open(file_name, "a") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writerow(data)


def init_save_files(file_names):
    """Initialize files used to save scraped data."""
    headers = ['id', 'name', 'wclass', 'rarity', 'hp', 'ammo_cost', 'ration_cost', 'damage', 'evasion', 'accuracy',
               'rof', 'move_speed', 'crit_rate', 'crit_damage', 'armor_pen', 'aura_tiles', 'aura_targets',
               'aura_buffs', 'armor', 'mag_size', 'aura_buff_vals']

    for file in file_names:
        with open(file, "w") as f:
            if file.endswith(".csv"):
                for header in headers:
                    f.write(header + ",")
                f.write("\n")
            elif file.endswith(".json"):
                f.write("[\n")
            else:
                pass


def clean_up(json_file):
    """Tying up some loose ends."""
    # Remove trailing comma from .json file
    with open(json_file, 'rb+') as filehandle:
        filehandle.seek(-2, os.SEEK_END)
        filehandle.truncate()

    # Write ']' to .json file to complete array of objects
    with open(json_file, "a", encoding='utf-8') as outfile:
        outfile.write("\n]")

    print("Data harvest complete. Check saves/ directory for results.")


if __name__ == "__main__":
    main()
