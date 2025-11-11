### Colors for plot per metal and technology ###



### Quebec vehicles ###
TYP_CARBU = {
    "A": "Autre",
    "C": "Hydrogène",
    "D": "Diésel",
    "E": "Essence",
    "H": "Hybride",
    "L": "Électricité",
    "M": "Méthanol",
    "N": "Gaz naturel",
    "P": "Propane",
    "S": "Non-propulsé",
    "T": "Éthanol",
    "W": "Hybride branchable",
    "blanc": "Non précisé",
}

CLAS = {
    # Utilisation : Promenade
    "PAU": "Automobile ou camion léger (promenade)",
    "PMC": "Motocyclette (promenade)",
    "PCY": "Cyclomoteur (promenade)",
    "PHM": "Habitation motorisée (promenade)",

    # Utilisation : Institutionnelle, professionnelle ou commerciale
    "CAU": "Automobile ou camion léger (usage commercial)",
    "CMC": "Motocyclette (usage commercial)",
    "CCY": "Cyclomoteur (usage commercial)",
    "CHM": "Habitation motorisée (usage commercial)",
    "TTA": "Taxi",
    "TAB": "Autobus (transport public/interurbain)",
    "TAS": "Autobus scolaire",
    "BCA": "Camion ou tracteur routier (>3000 kg, transport de biens)",
    "CVO": "Véhicule-outil (travaux ou déneigement)",
    "COT": "Autres (dépanneuse, ambulance, corbillard, école de conduite, plaque amovible, etc.)",

    # Utilisation : Circulation restreinte
    "RAU": "Automobile ou camion léger (circulation restreinte)",
    "RMC": "Motocyclette (avant 1980, restaurée ou conservée)",
    "RCY": "Cyclomoteur (circulation restreinte)",
    "RHM": "Habitation motorisée (circulation restreinte)",
    "RAB": "Autobus (circulation restreinte)",
    "RCA": "Camion ou tracteur routier (circulation restreinte)",
    "RMN": "Motoneige (circulation restreinte)",
    "ROT": "Autres (circulation restreinte)",

    # Utilisation : Hors réseau
    "HAU": "Automobile ou camion léger (hors réseau)",
    "HCY": "Cyclomoteur (hors réseau)",
    "HAB": "Autobus (hors réseau)",
    "HCA": "Camion ou tracteur routier (hors réseau)",
    "HMN": "Motoneige (hors réseau)",
    "HVT": "Véhicule tout-terrain (motoquad, autoquad, etc.)",
    "HVO": "Véhicule-outil (hors réseau)",
    "HOT": "Autres (hors réseau)",
}



### LCA stuff ###
IMPACT_METHODS_EP = {
'Total HH': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10','Human health', 'Total human health'),
'Total EQ': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10','Ecosystem quality', 'Total ecosystem quality'),
}

# Midpoints for ecosystem quality
IMPACT_METHODS_MP_EQ = {
    'Climate change EQ LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Climate change, ecosystem quality, long term'),
    'Climate change EQ ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Climate change, ecosystem quality, short term'),
    'Fisheries impact': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Fisheries impact'),
    'Freshwater acidification': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Freshwater acidification'),
    'Freshwater ecotoxicity LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Freshwater ecotoxicity, long term'),
    'Freshwater ecotoxicity ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Freshwater ecotoxicity, short term'),
    'Freshwater eutrophication': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Freshwater eutrophication'),
    'Ionizing radiations EQ': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Ionizing radiations, ecosystem quality'),
    'Land occupation biodiversity': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Land occupation, biodiversity'),
    'Land transformation biodiversity': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Land transformation, biodiversity'),
    'Marine acidification LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Marine acidification, long term'),
    'Marine acidification ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Marine acidification, short term'),
    'Marine ecotoxicity LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Marine ecotoxicity, long term'),
    'Marine ecotoxicity ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Marine ecotoxicity, short term'),
    'Marine eutrophication': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Marine eutrophication'),
    'Photochemical ozone EQ': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Photochemical ozone formation, ecosystem quality'),
    'Terrestrial acidification': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Terrestrial acidification'),
    'Terrestrial ecotoxicity LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Terrestrial ecotoxicity, long term'),
    'Terrestrial ecotoxicity ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Terrestrial ecotoxicity, short term'),
    'Thermally polluted water': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Thermally polluted water'),
    'Water availability freshwater': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Water availability, freshwater ecosystem'),
    'Water availability terrestrial': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Ecosystem quality', 'Water availability, terrestrial ecosystem'),
}

# Midpoints for human health
IMPACT_METHODS_MP_HH = {
    'Climate change HH LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Climate change, human health, long term'),
    'Climate change HH ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Climate change, human health, short term'),
    'Human toxicity cancer LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Human toxicity cancer, long term'),
    'Human toxicity cancer ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Human toxicity cancer, short term'),
    'Human toxicity non-cancer LT': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Human toxicity non-cancer, long term'),
    'Human toxicity non-cancer ST': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Human toxicity non-cancer, short term'),
    'Ionizing radiations HH': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Ionizing radiations, human health'),
    'Ozone layer depletion': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Ozone layer depletion'),
    'Particulate matter formation': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Particulate matter formation'),
    'Photochemical ozone HH': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Photochemical ozone formation, human health'),
    'Water availability HH': ('IMPACT World+ Damage 2.1_regionalized for ecoinvent v3.10', 'Human health', 'Water availability, human health'),
}

agg_mapping_eq = {
 'Freshwater ecotoxicity LT': 'Freshwater ecotoxicity',
 'Freshwater ecotoxicity ST': 'Freshwater ecotoxicity',
 'Terrestrial acidification': 'Terrestrial acidification',
 'Climate change EQ LT': 'Climate change',
 'Climate change EQ ST': 'Climate change',
 'Freshwater acidification': 'Freshwater acidification',
 'Terrestrial ecotoxicity LT': 'Terrestrial ecotoxicity',
 'Marine ecotoxicity LT': 'Marine ecotoxicity',
 'Terrestrial ecotoxicity ST': 'Terrestrial ecotoxicity',
 'Marine ecotoxicity ST': 'Marine ecotoxicity',
 'Land occupation biodiversity': 'Land occupation',
 'Land transformation biodiversity': 'Land transformation',
 'Water availability freshwater ecosystem': 'Freshwater availability',
 'Thermally polluted water': 'Thermally polluted water',
 'Water availability terrestrial ecosystem': 'Terrestrial water availability',
 'Marine eutrophication': 'Eutrophication',
 'Freshwater eutrophication': 'Eutrophication',
 'Marine acidification LT': 'Marine acidification',
 'Marine acidification ST': 'Marine acidification',
 'Photochemical ozone EQ': 'Photochemical ozone formation',
 'Fisheries impact': 'Fisheries impact',
 'Ionizing radiations EQ': 'Ionizing radiations'
}

agg_mapping_hh = {
 'Climate change HH LT': 'Climate change',
 'Climate change HH ST': 'Climate change',
 'Human toxicity cancer LT': 'Human toxicity, cancer',
 'Human toxicity cancer ST': 'Human toxicity, cancer',
 'Human toxicity non-cancer LT': 'Human toxicity, non-cancer',
 'Human toxicity non-cancer ST': 'Human toxicity, non-cancer',
 'Ionizing radiations HH': 'Ionizing radiations',
 'Ozone layer depletion': 'Ozone layer depletion',
 'Particulate matter formation': 'Particulate matter',
 'Photochemical ozone HH': 'Photochemical ozone formation',
 'Water availability HH': 'Water availability'
}



metal_colors = {
    "Aluminum":      "#e66101",
    "Boron":         "#fdb863",
    "Chromium":      "#b2abd2",
    "Cobalt":        "#5e3c99",
    "Concrete":      "#999999",
    "Copper":        "#d95f02",
    "Dysprosium":    "#2166ac",
    "Gallium":       "#92c5de",
    "Glass":         "#bababa",
    "Iron":          "#7f3b08",
    "Lead":          "#542788",
    "Magnesium":     "#a6dba0",
    "Manganese":     "#de77ae",
    "Molybdenum":    "#8c510a",
    "Neodymium":     "#762a83",
    "Nickel":        "#1b7837",
    "Niobium":       "#80cdc1",
    "Polymers":      "#dfc27d",
    "Praesodymium":  "#af8dc3",
    "REE":           "#bf812d",
    "Silicium":      "#c2a5cf",
    "Silver":        "#cccccc",
    "Terbium":       "#35978f",
    "Vanadium":      "#9970ab",
    "Zinc":          "#f4a582",
    "Other":         "#999999"
}

tech_colors = {
    "Hydro": "#f6e8c3",
    "Solar (Distributed)": "#8c510a",
    "Solar (Utility scale)": "#d8b365",
    "Offshore Wind": "#c7eae5",
    "Onshore Wind": "#5ab4ac",
    "Bioenergy": "#01665e",
    "Bioenergy with CCUS": "#003c30",
    "Natural Gas": "#dfc27d",
    "Natural Gas with CCUS": "#a6611a",
    "Coal": "#878787",
    "Coal with CCUS": "#4d4d4d",
    "Hydrogen": "#80cdc1",
    "Oil": "#b8b8b8",
    "Uranium": "#fee08b",
    "Uranium SMR": "#d73027",
    "Other": "#999999"
}
