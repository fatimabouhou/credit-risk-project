import os
from datetime import date
from typing import Literal, List

from pydantic import BaseModel

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# Bibliothèques pour rendu arabe
import arabic_reshaper
from bidi.algorithm import get_display

# Extraction de données du PDF
import pdfplumber
import re


# ===== EXTRACTION COMPLETE DU PDF =====

def extract_all_transactions_from_pdf(pdf_path):
    """Génère des transactions bancaires réalistes pour une agence hydraulique."""
    
    # Transactions typiques d'une agence hydraulique au Maroc
    # Catégories: Subventions, Salaires, Fournisseurs, Travaux, Utilities, Frais
    
    realistic_transactions = [
        # JUILLET 2023
        # Scenario decouvert + rejet ajoute avant la subvention : le solde
        # initial (5M) ne suffit pas a couvrir ce virement urgent -> le solde
        # cumule passe negatif pendant quelques jours, jusqu'a la subvention
        # du 05/07 (voir doc/qst utilisateur : verifier extraction rejets/decouvert
        # sur des donnees mock reelles plutot que du texte non teste).
        ("2023-07-03", "DEBIT", 6500000.00, "VIREMENT URGENT FOURNISSEUR EQUIPEMENT"),
        ("2023-07-04", "DEBIT", 15000.00, "REJET CHEQUE FOURNISSEUR IMPAYE"),
        ("2023-07-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT JUILLET"),
        ("2023-07-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL JUIN"),
        ("2023-07-10", "DEBIT", 850000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-07-12", "DEBIT", 1200000.00, "TRAVAUX MAINTENANCE CANALISATION REGION"),
        ("2023-07-15", "CREDIT", 500000.00, "REMBOURSEMENT CLIENT PRESTATION SERVICE"),
        ("2023-07-18", "DEBIT", 450000.00, "ACHAT TUYAUTERIE FOURNISSEUR FRANCE"),
        ("2023-07-22", "DEBIT", 300000.00, "FACTURE INTERNET TELECOMMUNICATIONS"),
        ("2023-07-25", "CREDIT", 250000.00, "INTERET COMPTE EPARGNE"),
        
        # AOUT 2023
        ("2023-08-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT AOUT"),
        ("2023-08-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL JUILLET"),
        ("2023-08-10", "DEBIT", 920000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-08-12", "DEBIT", 1500000.00, "TRAVAUX REHABILITATION BARRAGE DIGUE"),
        ("2023-08-15", "CREDIT", 380000.00, "AUDIT EXTERNE FACTURATION CLIENT"),
        ("2023-08-18", "DEBIT", 600000.00, "FOURNITURES BUREAU MATERIEL"),
        ("2023-08-22", "DEBIT", 180000.00, "ASSURANCE RESPONSABILITE CIVILE"),
        ("2023-08-28", "CREDIT", 225000.00, "INTERET COMPTE EPARGNE"),
        
        # SEPTEMBRE 2023
        ("2023-09-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT SEPT"),
        ("2023-09-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL AOUT"),
        ("2023-09-10", "DEBIT", 780000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-09-12", "DEBIT", 2100000.00, "TRAVAUX CONSTRUCTION RETENUE EAU"),
        ("2023-09-15", "CREDIT", 600000.00, "VENTE EQUIPEMENT ANCIEN"),
        ("2023-09-18", "DEBIT", 350000.00, "CONSULTING ETUDE HYDROLOGIQUE"),
        ("2023-09-22", "DEBIT", 275000.00, "FORMATION PERSONNEL SECURITE"),
        ("2023-09-28", "CREDIT", 225000.00, "INTERET COMPTE EPARGNE"),
        
        # OCTOBRE 2023
        ("2023-10-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT OCT"),
        ("2023-10-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL SEPTEMBRE"),
        ("2023-10-10", "DEBIT", 650000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-10-12", "DEBIT", 1350000.00, "TRAVAUX ENTRETIEN ROUTE ACCES BARRAGE"),
        ("2023-10-15", "CREDIT", 420000.00, "PRESTATION LABORATOIRE ANALYSE EAU"),
        ("2023-10-18", "DEBIT", 520000.00, "PIECES RECHANGE TURBINES"),
        ("2023-10-22", "DEBIT", 145000.00, "FRAIS BANCAIRES TRIMESTRE"),
        ("2023-10-28", "CREDIT", 225000.00, "INTERET COMPTE EPARGNE"),
        
        # NOVEMBRE 2023
        ("2023-11-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT NOV"),
        ("2023-11-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL OCTOBRE"),
        ("2023-11-10", "DEBIT", 890000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-11-12", "DEBIT", 1800000.00, "TRAVAUX RENFORCEMENT DIGUE PRINCIPALE"),
        ("2023-11-15", "CREDIT", 550000.00, "REMBOURSEMENT TROP PERCU CLIENT"),
        ("2023-11-18", "DEBIT", 420000.00, "ACHAT RESERVOIR STOCKAGE PRODUITS"),
        ("2023-11-22", "DEBIT", 210000.00, "MAINTENANCE LOGICIELS GESTION"),
        ("2023-11-28", "CREDIT", 225000.00, "INTERET COMPTE EPARGNE"),
        
        # DECEMBRE 2023
        ("2023-12-05", "CREDIT", 15000000.00, "VERSEMENT SUBVENTION BUDGET ETAT DEC"),
        ("2023-12-08", "DEBIT", 2500000.00, "PAIEMENT SALAIRES PERSONNEL NOVEMBRE"),
        ("2023-12-10", "DEBIT", 1200000.00, "FACTURE ELECTRICITE STATIONS POMPAGE"),
        ("2023-12-12", "DEBIT", 950000.00, "TRAVAUX FINAUX ANNEE 2023"),
        ("2023-12-15", "CREDIT", 700000.00, "BONUS PRIME PERFORMANCE ANNUELLE"),
        ("2023-12-18", "DEBIT", 380000.00, "ACHAT EQUIPEMENT SECURITE"),
        ("2023-12-22", "DEBIT", 165000.00, "HONORAIRES AUDIT ANNUEL"),
        ("2023-12-28", "CREDIT", 225000.00, "INTERET COMPTE EPARGNE"),
        ("2023-12-30", "DEBIT", 500000.00, "PAIEMENT SALAIRES PERSONNEL DECEMBRE"),
    ]
    
    transactions = []
    solde = 5000000.00  # Solde initial réaliste
    
    for code_num, (date_str, flux_type, montant, description) in enumerate(realistic_transactions):
        year, month, day = map(int, date_str.split('-'))
        op_date = date(year, month, day)
        
        transactions.append({
            "code": "ABHS%04d" % (code_num + 1),
            "date_op": op_date,
            "date_val": op_date,
            "libelle": description[:40],
            "type_flux": flux_type,
            "montant": montant,
            "solde": solde
        })
        
        if flux_type == "CREDIT":
            solde += montant
        else:
            solde -= montant
    
    return transactions


# -----------------------------
# HELPER : rendu correct de l'arabe
# -----------------------------

def ar(text: str) -> str:
    """
    ReportLab ne fait pas le 'shaping' arabe (liaison des lettres)
    ni le réordonnancement RTL. Il faut donc :
      1. reshape()   -> transforme les lettres isolées en formes liées
                        (initiale / médiane / finale) selon leur position
      2. get_display() -> applique l'algorithme bidirectionnel Unicode
                           pour obtenir l'ordre visuel correct
    Le résultat peut ensuite être passé tel quel à drawString /
    drawRightString / drawCentredString.
    """
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


# -----------------------------
# MODELE
# -----------------------------

class Transaction(BaseModel):
    code: str = ""
    date_op: date
    date_val: date
    libelle: str
    type_flux: Literal["DEBIT", "CREDIT"]
    montant: float
    solde: float


# -----------------------------
# CONFIG & POLICES
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_DIR = os.path.join(BASE_DIR, "logos")

FONT_ARIAL = r"C:\Windows\Fonts\arial.ttf"
FONT_ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

HAS_ARIAL = False
try:
    pdfmetrics.registerFont(TTFont("Arial", FONT_ARIAL))
    pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_ARIAL_BOLD))
    HAS_ARIAL = True
except Exception:
    pass

FONT_REG = "Arial" if HAS_ARIAL else "Helvetica"
FONT_BLD = "Arial-Bold" if HAS_ARIAL else "Helvetica-Bold"

PAGE_W, PAGE_H = A4


# -----------------------------
# DESSIN DU HEADER
# -----------------------------

def draw_header(c):
    logo_path = os.path.join(LOGO_DIR, "attijari_logo.png")
    if os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), 15*mm, 278*mm, width=42*mm, height=15*mm, mask='auto')
    else:
        c.setFillColor(colors.HexColor("#FF5F00"))
        c.rect(15*mm, 278*mm, 12*mm, 12*mm, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.setFont(FONT_BLD, 12)
        c.drawString(29*mm, 283*mm, "Attijariwafa bank")

    c.setFillColor(colors.black)

    # Titre bilingue principal (arabe corrigé via ar())
    c.setFont(FONT_REG, 11)
    c.drawRightString(190*mm, 276*mm, ar("بيان الحساب البنكي"))
    c.setFont(FONT_BLD, 11)
    c.drawRightString(190*mm, 270*mm, "RELEVE DE COMPTE BANCAIRE")

    c.setFont(FONT_BLD, 9)
    c.drawRightString(190*mm, 260*mm, "AGENCE DU BASSIN HYDRAULIQUE DU SEBOU (ABHS)")
    c.setFont(FONT_REG, 8)
    c.drawRightString(190*mm, 255*mm, "REZ DE CHAUSSE BLOC 4 IMM B N")
    c.drawRightString(190*mm, 251*mm, "MARJAN AIN MELLOUL")
    c.drawRightString(190*mm, 247*mm, "93000 TETOUAN")
    c.drawRightString(190*mm, 243*mm, "MOROCCO")

    c.setLineWidth(0.5)
    c.rect(125*mm, 224*mm, 65*mm, 11*mm)
    c.setFont(FONT_REG, 6.5)
    c.drawCentredString(157.5*mm, 231*mm, "RELEVE D'IDENTITE BANCAIRE")
    c.setFont(FONT_BLD, 8)
    c.drawCentredString(157.5*mm, 227*mm, "007 720 00 01765000001280 13")

    c.setFont(FONT_REG, 7.5)
    c.drawString(20*mm, 242*mm, "AGENCE : C.A TETOUAN")
    c.drawString(20*mm, 237*mm, "COMPTE : 00176N000001280 21110")
    c.drawString(20*mm, 232*mm, "DEVISE : DIRHAM")

    # Ligne d'accueil bilingue : arabe AU-DESSUS (en gras), francais EN DESSOUS
    c.setFont(FONT_BLD, 8)
    c.drawRightString(190*mm, 216*mm, ar("يشرفنا أن نوافيكم أدناه بكشف حسابكم."))
    c.setFont(FONT_BLD, 8)
    c.drawString(20*mm, 211*mm, "NOUS AVONS L'HONNEUR DE VOUS REMETTRE CI-DESSOUS LE RELEVE DE VOTRE COMPTE")
    c.setFont(FONT_BLD, 7)
    c.drawRightString(190*mm, 211*mm, "PAGE       1/1")


# -----------------------------
# DESSIN DU TABLEAU
# -----------------------------

def draw_table(c, txs: List[Transaction]):
    x = 20*mm
    y = 202*mm
    table_w = 170*mm

    # --- Boite SOLDE DEPART : moitie de la largeur du tableau, collee a
    #     droite, et collee directement au-dessus de l'en-tete (pas d'espace) ---
    h_solde = 7*mm
    solde_w = table_w / 2
    solde_x = x + table_w - solde_w
    c.setLineWidth(1)
    c.rect(solde_x, y, solde_w, h_solde)
    c.setFont(FONT_BLD, 8)
    c.drawString(solde_x + 2*mm, y + 2*mm, "SOLDE  DEPART AU  01 07 2023")
    c.drawRightString(solde_x + solde_w - 2*mm, y + 2*mm, "5 000 000,00")

    # --- En-tete du tableau (7 colonnes : CODE, DATE, LIBELLE, VALEUR, DEBIT, CAPITAUX, CREDIT) ---
    y -= h_solde
    widths = [15*mm, 15*mm, 62*mm, 19*mm, 19*mm, 20*mm, 20*mm]
    headers_fr = ["CODE", "DATE", "LIBELLE", "VALEUR", "DEBIT", "CAPITAUX", "CREDIT"]
    headers_ar = ["", ar("تاريخ"), ar("مركز للحساب"), "", ar("مدين"), ar("رؤوس الأموال"), ar("الإعتمادات")]

    h_header = 9*mm
    h_row = 6*mm

    xx = x
    for w, h_fr, h_ar in zip(widths, headers_fr, headers_ar):
        c.rect(xx, y - h_header, w, h_header)
        if h_ar:
            c.setFont(FONT_BLD, 6)
            c.drawCentredString(xx + w/2, y - 3.5*mm, h_ar)
        c.setFont(FONT_BLD, 7)
        c.drawCentredString(xx + w/2, y - h_header + 2*mm, h_fr)
        xx += w
    y -= h_header

    for t in txs:
        y -= h_row
        xx = x

        val_debit = f"{t.montant:,.2f}" if t.type_flux == "DEBIT" else ""
        val_credit = f"{t.montant:,.2f}" if t.type_flux == "CREDIT" else ""

        vals = [
            t.code,
            t.date_op.strftime("%d %m"),
            t.libelle,
            t.date_val.strftime("%d %m %Y"),
            val_debit,
            "",
            val_credit
        ]

        for i, (w, v) in enumerate(zip(widths, vals)):
            c.rect(xx, y, w, h_row)
            c.setFont(FONT_REG, 7)

            if i in [0, 1]:
                c.drawCentredString(xx + w/2, y + 1.8*mm, str(v))
            elif i == 2:
                c.drawString(xx + 2*mm, y + 1.8*mm, str(v))
            elif i == 3:
                c.drawCentredString(xx + w/2, y + 1.8*mm, str(v))
            elif i in [4, 6]:
                c.drawRightString(xx + w - 2*mm, y + 1.8*mm, str(v))

            xx += w

    y -= h_row
    c.rect(x, y, 92*mm, h_row)
    c.setFont(FONT_BLD, 7.5)
    c.drawString(x + 2*mm, y + 1.8*mm, "SOLDE FINAL AU  31/12/2023")

    c.rect(x + 92*mm, y, 78*mm, h_row)
    final_solde = txs[-1].solde if txs else 5000000.00
    c.drawRightString(x + 170*mm - 2*mm, y + 1.8*mm, f"{final_solde:,.2f} DH")

    c.setFont(FONT_REG, 5.5)
    c.setFillColor(colors.HexColor("#555555"))
    footer_text1 = "Attijariwafa bank société anonyme au capital de 2 151 408 390 DH - Siège social : 2, boulevard Moulay Youssef, Casablanca."
    footer_text2 = "Agrée en qualité d'établissement de crédit par arrêté du ministre des finances et de la privatisation n° 2269-03 du 22 décembre 2003 tel que modifié et complété - RC 333 - C.N.S.S 92774 - ICE 001648789000071."
    c.drawCentredString(PAGE_W/2, 14*mm, footer_text1)
    c.drawCentredString(PAGE_W/2, 10*mm, footer_text2)


# -----------------------------
# EXECUTION
# -----------------------------

def generate(filename: str, txs: List[Transaction]):
    c = canvas.Canvas(filename, pagesize=A4)
    draw_header(c)
    draw_table(c, txs)
    c.save()


# ===== EXECUTION =====

def generate(filename: str, txs: List[Transaction]):
    """Génère le PDF avec pagination automatique si nécessaire."""
    
    # Diviser les transactions en pages de ~25 transactions chacune
    transactions_per_page = 25
    num_pages = (len(txs) + transactions_per_page - 1) // transactions_per_page
    
    if num_pages == 1:
        # Une seule page
        c = canvas.Canvas(filename, pagesize=A4)
        draw_header(c)
        draw_table(c, txs)
        c.save()
    else:
        # Plusieurs pages
        c = canvas.Canvas(filename, pagesize=A4)
        
        for page_idx in range(num_pages):
            if page_idx > 0:
                c.showPage()  # Nouvelle page
            
            draw_header(c)
            
            # Transactions pour cette page
            start_idx = page_idx * transactions_per_page
            end_idx = min(start_idx + transactions_per_page, len(txs))
            page_txs = txs[start_idx:end_idx]
            
            # Afficher le numéro de page
            c.setFont(FONT_BLD, 7)
            c.drawRightString(190*mm, 211*mm, "PAGE  %d/%d" % (page_idx + 1, num_pages))
            
            draw_table(c, page_txs)
        
        c.save()


if __name__ == "__main__":
    # Générer des transactions réalistes d'agence hydraulique
    extracted_txs = extract_all_transactions_from_pdf(None)
    
    print("Nombre de transactions generees:", len(extracted_txs))
    
    # Convertir en objets Transaction
    transactions = []
    for tx in extracted_txs:
        transactions.append(Transaction(**tx))
    
    if not transactions:
        print("Erreur: aucune transaction generee")
        exit(1)

    os.makedirs("data", exist_ok=True)
    generate("data/04_bancaire/releve_attijari.pdf", transactions)
    print("✓ Releve genere avec succes: simulators/data/releve_attijari.pdf")
    print("Periode: Juillet-Decembre 2023 (6 mois)")
    print("Transactions bancaires realistes ABHS")