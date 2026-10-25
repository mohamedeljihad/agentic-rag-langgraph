"""Tests rapides des composants déterministes (sans LLM) : python -m pytest -q"""
from src.ingestion import charger_corpus, construire_chunks
from src.nodes import _CALCUL, _QUANTITE, route_apres_evaluation, route_apres_glossaire
from src.tools import calculatrice, consulter_glossaire, normaliser_nombres, termes_glossaire
from src.evaluate import fait_present


def test_corpus_et_decoupage():
    docs = charger_corpus()
    assert len(docs) == 15
    chunks = construire_chunks(docs)
    assert all(50 < len(c.texte) <= 800 for c in chunks)
    assert {c.doc_id for c in chunks} == {d.doc_id for d in docs}


def test_calculatrice_sure():
    assert calculatrice.invoke({"expression": "max(20000000, 0.04*1000000000)"}) == "40 000 000"
    assert calculatrice.invoke({"expression": "__import__('os')"}).startswith("ERREUR")
    assert calculatrice.invoke({"expression": "7*3"}) == "21"


def test_glossaire():
    assert consulter_glossaire.invoke({"terme": "mfa"}).startswith("MFA")
    assert consulter_glossaire.invoke({"terme": "XYZ"}) == "INCONNU"
    assert "CNDP" in termes_glossaire("Que fait la CNDP ?")


def test_normalisation_nombres():
    assert normaliser_nombres("1 milliard d'euros et 1,4 %") == "1000000000 d'euros et 1.4 %"


def test_detection_calcul():
    q = "Une entité a un chiffre d'affaires de 2 milliards d'euros : calculez le plafond d'amende."
    assert _CALCUL.search(q) and _QUANTITE.search(q)
    assert not _QUANTITE.search("Combien de mesures contient l'ISO 27001 version 2022 ?")


def _doc(cid, pert, origine):
    return {"chunk_id": cid, "doc_id": cid[:3], "score": 0.85, "pertinent": pert, "requete": origine,
            "origines": [origine], "texte": "x"}


def test_boucle_de_reecriture():
    etat = {"question": "q", "sous_questions": ["a ?", "b ?"], "nb_reecritures": 0, "besoin_calcul": False,
            "documents": [_doc("D01-c0", True, "a ?"), _doc("D02-c0", False, "b ?")]}
    assert route_apres_evaluation(etat) == "reecrire"            # « b ? » non couverte
    etat["nb_reecritures"] = 2
    assert route_apres_evaluation(etat) == "generer"             # budget épuisé
    etat.update(nb_reecritures=1, nouveaux=0)
    assert route_apres_evaluation(etat) == "generer"             # stagnation : rien de nouveau
    etat.update(nb_reecritures=0, besoin_calcul=True, documents=[_doc("D01-c0", True, "a ?"), _doc("D02-c0", True, "b ?")])
    assert route_apres_evaluation(etat) == "calculer"


def test_route_glossaire():
    assert route_apres_glossaire({"reponse": "def"}) == "trouve"
    assert route_apres_glossaire({"reponse": ""}) == "non_trouve"


def test_metrique_faits():
    assert fait_present("amende de 40 000 000 €", ["40 millions", "40000000"])
    assert not fait_present("score 7,5", ["7"])
