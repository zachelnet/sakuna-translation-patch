# Deutsche Uebersetzungen: Param/Item/Enchant.csv (173 Name/Beschreibung-Paare)
#
# Reihen 22-49 (Jahreszeiten-Booster), 113-116, 117-126 (Feindtypen) und
# 154-161 (Sammler) folgen festen Mustern und werden erzeugt.

_PATH = "Param/Item/Enchant.csv"
_PAIRS: list = []

# 1-21  Steigerungen und Stärkungen
_PAIRS += [
    ("LP-Steigerung", "Erhöht LP um ~ItemParameter~"),
    ("LP-Steigerung +", "Erhöht LP um ~ItemParameter~"),
    ("SP-Steigerung", "Erhöht SP um ~ItemParameter~"),
    ("SP-Steigerung-Splitter", "Erhöht SP um ~ItemParameter~"),
    ("Stärke-Steigerung", "Erhöht die Stärke um ~ItemParameter~"),
    ("Stärke-Steigerung +", "Erhöht die Stärke um ~ItemParameter~"),
    ("Vitalitäts-Steigerung", "Erhöht die Vitalität um ~ItemParameter~"),
    ("Vitalitäts-Steigerung +", "Erhöht die Vitalität um ~ItemParameter~"),
    ("Magie-Steigerung", "Erhöht die Magie um ~ItemParameter~"),
    ("Magie-Steigerung +", "Erhöht die Magie um ~ItemParameter~"),
    ("Glücks-Steigerung", "Erhöht das Glück um ~ItemParameter~"),
    ("Glücks-Steigerung +", "Erhöht das Glück um ~ItemParameter~"),
    ("Appetit-Steigerung", "Erhöht den Appetit um ~ItemParameter~"),
    ("Appetit-Steigerung +", "Erhöht den Appetit um ~ItemParameter~"),
    ("LP-Boost", "Erhöht LP um ~Value~%"),
    ("SP-Boost", "Erhöht SP um ~Value~%"),
    ("Stärke-Boost", "Erhöht die Stärke um ~Value~%"),
    ("Vitalitäts-Boost", "Erhöht die Vitalität um ~Value~%"),
    ("Magie-Boost", "Erhöht die Magie um ~Value~%"),
    ("Glücks-Boost", "Erhöht das Glück um ~Value~%"),
    ("Appetit-Boost", "Erhöht den Appetit um ~Value~%"),
]

# 22-49  Jahreszeiten-Booster (4 Jahreszeiten x 7 Werte)
_STAT = [
    ("Health", "LP", "Erhöht LP"),
    ("Skill", "SP", "Erhöht SP"),
    ("Strength", "Stärke", "Erhöht die Stärke"),
    ("Vitality", "Vitalität", "Erhöht die Vitalität"),
    ("Magic", "Magie", "Erhöht die Magie"),
    ("Luck", "Glück", "Erhöht das Glück"),
    ("Gusto", "Appetit", "Erhöht den Appetit"),
]
_SEASON = [("Spring", "Frühling"), ("Summer", "Sommer"),
           ("Autumn", "Herbst"), ("Winter", "Winter")]
for _en_s, _de_s in _SEASON:
    for _en_st, _de_st, _verb in _STAT:
        _PAIRS.append((f"{_de_s}-{_de_st}-Boost",
                       f"{_verb} im {_de_s} um ~Value~%"))

# 50-112  Einzel-Effekte
_PAIRS += [
    ("SP-, Magie- und Glücks-Boost", "Erhöht SP und steigert Magie und Glück um ~Value~%"),
    ("LP-, Stärke- und Vitalitäts-Boost", "Erhöht LP und steigert Stärke und Vitalität um ~Value~%"),
    ("Natürliche Heilung", "Stellt LP außerhalb des Kampfes fortlaufend her"),
    ("Über-Gourmet", "Erhöht die Wirkung von Mahlzeiten um ~Value~%"),
    ("Schnelle Erholung", "LP-Erholung steigt auf ~ValueRate+1~x ihres Normalwerts"),
    ("Wiederbelebung", "Einmal täglich wird LP um ~Value~% wiederhergestellt, wenn du besiegt wirst"),
    ("Bestform", "Erhöht die Stärke um ~Value~%, wenn LP voll ist"),
    ("Entkräftung", "Verringert den zugefügten Schaden um ~Value~%"),
    ("Unaufhaltsam", "Verringert den Schaden durch Projektile um ~Value~%"),
    ("Fallenschutz", "Verringert den Umgebungsschaden um ~Value~%"),
    ("Verwundbarkeit", "Erhöht den erlittenen Feindschaden um ~Value~%"),
    ("Waffenverstärkung", "Erhöht den Angriff der angelegten Waffe um ~Value~%"),
    ("Waffenverstärkung", "Erhöht den Angriff der angelegten Waffe um ~ItemParameter~"),
    ("Granit-Waffenverstärkung", "Erhöht den Angriff von Granitwaffen um ~ValueRate+1~x"),
    ("Dämonisches Erwachen", "Erhöht den Angriff dämonischer Waffen abhängig von deiner Magie"),
    ("Kampffieber", "Erhöht den Angriff abhängig von der Zahl besiegender Feinde"),
    ("Besenstiel-Erwachen", "Erhöht den Angriff des Bambusbesens abhängig von deiner Magie"),
    ("Kraft-Boost für Einhandwaffen", "Erhöht die verborgenen Kraft-Effekte von Einhandwaffen um ~Value~%"),
    ("Kraft-Boost für Zweihandwaffen", "Erhöht die verborgenen Kraft-Effekte von Zweihandwaffen um ~Value~%"),
    ("Kraft-Boost für Kleidung", "Erhöht die verborgenen Kraft-Effekte von Kleidung um ~Value~%"),
    ("Kraft-Boost für Kopfschutz", "Erhöht die verborgenen Kraft-Effekte von Kopfschutz um ~Value~%"),
    ("Kraft-Boost für Masken", "Erhöht die verborgenen Kraft-Effekte von Masken um ~Value~%"),
    ("Kraft-Boost für Granitwaffen", "Erhöht die verborgenen Kraft-Effekte von Granitwaffen um ~Value~%"),
    ("Letztes Aufgebot", "Erhöht den zugefügten Schaden um ~Value~% um den Preis der LP-Erholung"),
    ("Lebenssauger", "Stellt ~Value~% LP wieder her, wenn ein Feind besiegt wird"),
    ("Energiesauger", "Erhöht vorübergehend den zugefügten Schaden um ~Value~% je besiegem Feind"),
    ("Vergeltung", "Stellt LP um ~Value~% wieder her, wenn eine Feindgruppe besiegt wird"),
    ("Seelenleben", "Stellt LP um ~Value~% wieder her, wenn du Bernstein erhältst"),
    ("Seelentechnik", "Stellt SP um ~Value~% wieder her, wenn du Bernstein erhältst"),
    ("Besonnenheit", "Verringert die Kosten besonderer Angriffe um ~Value~%"),
    ("Göttliche Besonnenheit", "Verringert die Kosten von Gewandtechniken um ~Value~%"),
    ("Volle Fahrt", "Besondere Angriffe kosten doppelt, fügen aber ~Value~% mehr Schaden zu"),
    ("Geistiges Auge", "Erhöht die kritische Trefferchance um ~Value~%"),
    ("Kletterrausch", "Erhöht die kritische Trefferchance um ~Value~% je Kombo-Treffer"),
    ("Volle Power", "Erhöht die kritische Trefferkraft um ~Value~%"),
    ("Vitaler Schlag", "Kritische Treffer lösen einen Attributvorteil aus"),
    ("Eiserne Mauer", "Erhöht die Chance, Schutzschild zu aktivieren, um ~Value~%"),
    ("Kettenkombo", "Füge bis zu ~Value~% mehr Schaden pro aufeinanderfolgendem Angriff zu"),
    ("Tanzender Schmetterling", "Fügt ~Value~% mehr Schaden zu, wenn du und der Feind in der Luft seid"),
    ("Auflösender Schlag", "Fügt dem Feind ~ValueRate+1~x mehr Schaden auf seiner Haltbarkeitsstufe zu"),
    ("Durchdringung", "Verringert die Verteidigung der Feinde um ~Value~%"),
    ("Katapultierte Wucht", "Fügt ~ValueRate+1~x mehr Schaden zu, wenn der Feind weggeworfen wird"),
    ("Wütender Bö", "Verdoppelt die Aufprallkraft, senkt aber andere Angriffe um 30%"),
    ("Gegenstoß", "Erhöht vorübergehend den Schaden um ~Value~% nach einem Pari"),
    ("Unangreifbar", "Verringert vorübergehend den erlittenen Schaden um ~Value~% nach einem Pari"),
    ("Umkehr", "Verlängert die Betäubung nach einem Pari um ~ValueRate+1~x"),
    ("Fokus", "Verlängert das Zeitfenster zum Parieren um ~ValueRate+1~x"),
    ("Gelassenheit", "~Value~% Chance, Feindangriffe automatisch zu parieren"),
    ("Strahlende Tugend", "Erhöht den Attributeffekt der angelegten Waffe um ~ValueRate+1~x"),
    ('Schlag-Amulett', 'Ändert das Attribut der angelegten Waffe zu "Schlag"'),
    ('Schnitt-Amulett', 'Ändert das Attribut der angelegten Waffe zu "Schnitt"'),
    ('Stich-Amulett', 'Ändert das Attribut der angelegten Waffe zu "Stich"'),
    ('Magie-Amulett', 'Ändert das Attribut der angelegten Waffe zu "Magie"'),
    ('Kein-Amulett', 'Ändert das Attribut der angelegten Waffe zu "Kein"'),
    ("Schlagabwehr", "Verringert den Schaden durch Schlagangriffe um ~Value~%"),
    ("Schnittabwehr", "Verringert den Schaden durch Schnittangriffe um ~Value~%"),
    ("Stichabwehr", "Verringert den Schaden durch Stichangriffe um ~Value~%"),
    ("Magieabwehr", "Verringert den Schaden durch Magieangriffe um ~Value~%"),
    ("Neutralabwehr", "Verringert den Schaden durch Angriffe ohne Attribut um ~Value~%"),
    ("Abwehr ohne Element", "Verringert den Schaden durch Angriffe ohne Attribut um ~Value~%"),
    ("Feuerabwehr", "Verringert den Schaden durch Feuerangriffe um ~Value~%"),
    ("Wasserabwehr", "Verringert den Schaden durch Wasserangriffe um ~Value~%"),
    ("Giftabwehr", "Verringert den Schaden durch Giftangriffe um ~Value~%"),
]

# 113-116  Waffe stärken (4x identisch)
for _ in range(4):
    _PAIRS.append(("Waffe stärken", "Erhöht die Kraft von ~SkillName~ um ~ValueRate+1~x"))

# 117-126  Feindtypen (zwei identische Bloecke)
_RACE = [
    ("Geißel der Zweibeiner", "Fügt zweibeinigen Feinden ~ValueRate+1~x mehr Schaden zu"),
    ("Unheil der Vierbeiner", "Fügt vierbeinigen Feinden ~ValueRate+1~x mehr Schaden zu"),
    ("Flügelschneider", "Fügt fliegenden Feinden ~ValueRate+1~x mehr Schaden zu"),
    ("Kiemenzerfetzer", "Fügt wassernahen Feinden ~ValueRate+1~x mehr Schaden zu"),
    ("Gespenstergeißel", "Fügt Gespenstern ~ValueRate+1~x mehr Schaden zu"),
]
_PAIRS += _RACE + _RACE

# 127-153
_PAIRS += [
    ("Göttlichkeit", "Verwandelt stärkebasierte Angriffe in magiebasierte"),
    ("Muckibau", "Verwandelt magiebasierte Angriffe in stärkebasierte"),
    ("Himmlische Maid", "Erhöht die Wirkung von Gewandtechniken um ~ValueRate+1~x"),
    ("Chaotische Heimsuchung", "Ändert bei jedem Einsatz die Wirkung von Jenseitiger Schwächung"),
    ("Vollauf", "Verringert die Hungerate um ~Value~%"),
    ("Doppeltverdauung", "Verdoppelt die Hungerate, erhöht aber die Essenseffekte um ~Value~%"),
    ("Tollkühn", "Desto weniger LP du hast, desto mehr Schaden (bis ~ValueRate+1~x)"),
    ("Gierig", "Desto hungriger du bist, desto mehr Schaden (bis ~ValueRate+1~x)"),
    ("Doppelschneidiges Schwert", "Erhält doppelt so viel Schaden, fügt aber ~Value~% mehr zu"),
    ("Berserker", "Kein Zucken mehr, wenn du beim Angriff Schaden erleidest"),
    ("Geldschild", "~Value~% Chance, Schaden durch Verbrauch von Bernstein abzuwenden"),
    ("Goldene Waage", "Erhöht das Glück abhängig von deinem Gesamtbernstein"),
    ("Sonnengöttin", "Fügt bei sonnigem Wetter ~Value~% mehr Schaden zu"),
    ("Regengöttin", "Fügt bei regnerischem Wetter ~Value~% mehr Schaden zu"),
    ("Schneegöttin", "Fügt bei schneeiem Wetter ~Value~% mehr Schaden zu"),
    ("Nachteule", "Fügt nachts ~Value~% mehr Schaden zu"),
    ("Meerjungfrau", "Erhöht Angriff und Verteidigung um ~Value~% im Wasser"),
    ("Scharfes Auge", "Benachrichtigt dich, wenn Schatz in der Nähe ist"),
    ("Disziplin", "Erhöht die Technik-Erfahrung um ~Value~%"),
    ("Berühmter Bauer", "Erhöht die Erfahrung aus der Feldarbeit um ~Value~%"),
    ("Mogul", "Feinde lassen ~Value~% mehr Bernstein fallen"),
    ("Kostlaunigkeit", "Feinde lassen ~Value~% weniger Bernstein fallen"),
    ("Jägerin", "Feinde lassen ~Value~% mehr Fleisch fallen"),
    ("Kenner", "Feinde lassen ~ValueRate+1~x mehr Materialien fallen"),
    ("Glückstreffer", "Feinde lassen ~ValueRate+1~x mehr Beute fallen"),
    ("Bergmann", "Beim Erhalt von Erzen steigt deine Ausbeute um ~Value~%"),
    ("Kräuterkundin", "Beim Erhalt von Pflanzen steigt deine Ausbeute um ~Value~%"),
]

# 154-161  Sammler (+/-)
_COLLECT = [("Zutaten", "Zutatensammler"), ("Erze", "Erzsammler"),
            ("Textilien und Farben", "Textil-/Farbsammler"), ("Mist", "Mistsammler")]
for _what, _name in _COLLECT:
    _PAIRS.append((f"{_name} +", f"Erhöht die Sammelrate für {_what} um ~Value~%"))
    _PAIRS.append((f"{_name} −", f"Verringert die Sammelrate für {_what} um ~Value~%"))

# 162-173
_PAIRS += [
    ("Perlige Paarung", "Kombiniert mit einer Dämonenperle für ~Value~% mehr Schaden"),
    ("Überfluss", "Erhöht die Kraft aller Fähigkeiten um ~Value/10~% deiner Gesamternte"),
    ("Dämonenzug", "Erhöht das Level aller Dämonen"),
    ("Gesundheitsverseuchung", "LP um ~Value~% reduziert"),
    ("Technikverseuchung", "SP um ~Value~% reduziert"),
    ("Sättigungsverseuchung", "Sättigung um ~Value~% reduziert"),
    ("Stärkeverseuchung", "Stärke um ~Value~% reduziert"),
    ("Vitalitätsverseuchung", "Vitalität um ~Value~% reduziert"),
    ("Magieverseuchung", "Magie um ~Value~% reduziert"),
    ("Glücksverseuchung", "Glück um ~Value~% reduziert"),
    ("Esslustverseuchung", "Appetit um ~Value~% reduziert"),
    ("Omizuchis Verderben", "Durchschlägt Omizuchis Schuppen"),
]

assert len(_PAIRS) == 173, f"erwartet 173 Paare, gefunden {len(_PAIRS)}"

DE_ENCHANT: dict = {}
for _i, (_n, _c) in enumerate(_PAIRS, 1):
    DE_ENCHANT[(_PATH, f"NameEn#{_i}")] = _n
    DE_ENCHANT[(_PATH, f"CommentEn#{_i}")] = _c
