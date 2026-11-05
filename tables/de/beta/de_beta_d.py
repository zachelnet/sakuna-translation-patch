# Deutsche Beta-Uebersetzungen (Teil D): β2-Kleinteile (47)
# Mura(5) Kaji/EventMain(2) RoomWoman(2) Naya(18) Hataori/Yui(20)

_FILES = {
"Text/Event/Mura/Mura.csvtxt": [
    (26, '~AttackWButton~ Rasten'),
    (27, 'Jetzt keine Rast möglich'),
    (28, '~Time~ Stunden rasten'),
    (29, '~DecideButton~ Rasten  ~CancelButton~ Beenden'),
    (30, '~CancelButton~ Rast beenden'),
],
"Text/Event/Mura/Kaji/EventMain.csvtxt": [
    (63, 'Aus irgendeinem Grund hast du die Sichel des Hoshidama bereits.'),
    (64, 'Seltsamerweise hast du die Hacke des Hoshidama bereits.'),
],
"Text/Event/Mura/RoomWoman/EventSub.csvtxt": [
    (30, 'Aaaaaaargh! Wa-ha-haaaugh!'),
    (31, 'Was für ein Lärm...'),
],
"Text/Event/Mura/Naya/EventSub.csvtxt": [
    (90, 'Oh... Erstaunlich! Du reparierst die Hacke!'),
    (91, 'Mmm... Mit Hilfe, ja. Ich schätze, das ist alles,\nwas ich kann.'),
    (92, 'Kinta... Du nicht glücklich?'),
    (93, 'Nein...'),
    (94, 'Kinta?'),
    (95, 'Urgh...'),
    (96, 'Kinta, du großartig. Sogar sehr.'),
    (97, 'N-Nah, ich bin nicht...'),
    (98, 'Bitte sag, was du essen möchtest, wenn du müde bin.\nIch mache gutes Essen.'),
    (99, '...'),
    (100, 'Kinta... ist leise.'),
    (101, 'N-Nein bin ich nicht.'),
    (102, 'Du hasst es, mit mir zu reden?'),
    (103, 'Nah, so ist es nicht.'),
    (104, 'Ay...nt?'),
    (105, 'Agh! Schluss schon!'),
    (106, 'Oh! Auf Wiedersehen...?'),
    (107, 'Kinta schwierig.'),
],
"Text/Event/Mura/Hataori/Yui.csvtxt": [
    (54, 'Yui. Diese neuen Gewänder deiner tragen anscheinend\nden köstlichsten Duft.'),
    (55, 'Oh, gemerkt?! Lady Kokorowa hat mir beigebracht,\nwie man sie parfümiert.'),
    (56, 'Ho... „Parfümieren", sagst du?'),
    (57, 'Du trocknest die vom Färben übrig gebliebenen\nBlätter, schneidest sie klein und steckst sie in\neinen Sack. Nach ein paar Tagen hat das Gewand\neinen schönen Duft.'),
    (58, 'Du bist bereit, Zeit und Mühe dafür aufzuwenden?\nWie großzügig von dir!'),
    (59, 'Nun, ich habe noch die Angewohnheit, Pflanzen\nund Kräuter zu pflücken, wann immer ich Sammeln bin.'),
    (60, 'Haha. Sieht so aus.'),
    (61, 'Welche Arten von Pflanzen nimmst du also zum Parfümieren?'),
    (62, 'Ich habe sie hier hinten. Komm rein.'),
    (63, 'Wenn ich süßen Duft will, nehme ich diesen\nBeifuß hier. Der ist auf deinen Gewändern,\nGöttin.'),
    (64, 'Das hier ist Gardenie. Sie hat starken Duft,\ndeshalb musst du aufpassen, nur ein bisschen zu nehmen.\nIch benutze sie für Myrthes Gewänder.'),
    (65, 'Bei Beifuß kannst du zusätzlich zum Blatt\nden Stängel verwenden. Es ist irgendwie wie Mochi,\nalso perfekt für Mister Tauemon.'),
    (66, 'Ich bekomme Nelken und weißen Sandelholz von\nLady Kokorowa.'),
    (67, 'Ich hatte keine Ahnung, dass es so viele Sorten gibt!\nDas fühlt sich sicherlich schon viel mehr\nnach einem Mädchenzimmer an.'),
    (68, 'Hee hee... Weißt du, die Schmiedehütte nebenan\nwird heiß und stickig.'),
    (69, 'Ich frage mich, welcher Duft Kinta am besten gefallen würde.'),
    (70, 'Ich bezweifle, dass er schon Sinn für so etwas hat,\naber wenn wir ihn sich selbst überlassen,\nwäscht er sich nie, also...'),
    (71, 'Ich hoffe, er trägt es ohne großes Aufheben.'),
    (72, 'Na, Blumen fallen wohl raus.'),
    (73, 'Hmmm... Dann vielleicht Zeder...'),
],
}

DE_BETA_D = {}
_RANGES = {
    "Text/Event/Mura/Mura.csvtxt": (26, 30),
    "Text/Event/Mura/Kaji/EventMain.csvtxt": (63, 64),
    "Text/Event/Mura/RoomWoman/EventSub.csvtxt": (30, 31),
    "Text/Event/Mura/Naya/EventSub.csvtxt": (90, 107),
    "Text/Event/Mura/Hataori/Yui.csvtxt": (54, 73),
}
for _p, _pairs in _FILES.items():
    _a, _b = _RANGES[_p]
    assert [r for r, _ in _pairs] == list(range(_a, _b + 1)), _p
    DE_BETA_D.update({(_p + "#beta", f"English#{r}"): t for r, t in _pairs})
assert len(DE_BETA_D) == 47, len(DE_BETA_D)
