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

import arabic_reshaper
from bidi.algorithm import get_display


# ===== GENERATION DE TRANSACTIONS REALISTES =====

def extract_all_transactions_from_cih():
    """Génère des transactions bancaires réalistes pour compte CIH (crédit immobilier)."""
    
    # Transactions typiques d'un compte CIH pour une agence hydraulique
    # CIH = crédit immobilier -> emprunts, remboursements, intérêts
    
    realistic_transactions = [
        # JUILLET 2023
        # Scenario decouvert + rejet : le solde initial (10M) ne suffit pas a
        # couvrir ce virement urgent -> solde cumule negatif quelques jours,
        # jusqu'au versement du 05/07 (memes scenarios que le mock Attijari,
        # pour verifier l'extraction rejets/decouvert sur les 2 formats reels).
        ("2023-07-02", "DEBIT", 11500000.00, "VIREMENT URGENT TRAVAUX BARRAGE"),
        ("2023-07-03", "DEBIT", 20000.00, "REJET PRELEVEMENT IMPAYE FOURNISSEUR"),
        ("2023-07-05", "CREDIT", 8000000.00, "VERSEMENT PROJET CONSTRUCTION BARRAGE"),
        ("2023-07-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-07-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-07-22", "DEBIT", 125000.00, "FRAIS DOSSIER CREDIT CIH"),
        
        # AOUT 2023
        ("2023-08-05", "CREDIT", 8000000.00, "VERSEMENT PHASE 2 CONSTRUCTION BARRAGE"),
        ("2023-08-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-08-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-08-28", "CREDIT", 150000.00, "REMBOURSEMENT COMMISSION ERROR CIH"),
        
        # SEPTEMBRE 2023
        ("2023-09-05", "CREDIT", 8000000.00, "VERSEMENT PHASE 3 CONSTRUCTION BARRAGE"),
        ("2023-09-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-09-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-09-22", "DEBIT", 85000.00, "ASSURANCE CREDIT IMMOBILIER"),
        
        # OCTOBRE 2023
        ("2023-10-05", "CREDIT", 8000000.00, "VERSEMENT PHASE 4 CONSTRUCTION BARRAGE"),
        ("2023-10-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-10-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-10-30", "CREDIT", 75000.00, "REMBOURSEMENT FRAIS ADMINISTRATIFS"),
        
        # NOVEMBRE 2023
        ("2023-11-05", "CREDIT", 8000000.00, "VERSEMENT PHASE 5 CONSTRUCTION BARRAGE"),
        ("2023-11-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-11-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-11-25", "DEBIT", 120000.00, "FRAIS FINANCEMENT CREDIT"),
        
        # DECEMBRE 2023
        ("2023-12-05", "CREDIT", 8000000.00, "VERSEMENT PHASE 6 CONSTRUCTION BARRAGE"),
        ("2023-12-10", "DEBIT", 250000.00, "REMBOURSEMENT INTERET PRET IMMOBILIER"),
        ("2023-12-15", "DEBIT", 1500000.00, "REMBOURSEMENT CAPITAL PRET BARRAGE"),
        ("2023-12-20", "CREDIT", 250000.00, "COMPENSATION CREDIT BANCAIRE"),
        ("2023-12-28", "DEBIT", 95000.00, "FRAIS GESTION COMPTE CREDIT"),
    ]
    
    transactions = []
    solde = 10000000.00  # Solde initial pour compte crédit immobilier
    
    for code_num, (date_str, flux_type, montant, description) in enumerate(realistic_transactions):
        year, month, day = map(int, date_str.split('-'))
        op_date = date(year, month, day)
        
        transactions.append({
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
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


# -----------------------------
# MODELE
# -----------------------------
class Transaction(BaseModel):
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
# DESSIN DU HEADER CIH BANK
# -----------------------------
def draw_header(c):
    # 1. Chargement du logo uniquement en TOP À GAUCHE (sans étirement)
    logo_path = os.path.join(LOGO_DIR, "cih_logo.png")
    if os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), 15*mm, 274*mm, width=52*mm, height=13*mm, mask='auto')
    else:
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#1A1A1A"))
        c.drawString(15*mm, 280*mm, "CIH")
        c.setFillColor(colors.HexColor("#009EE0"))
        c.drawString(26*mm, 280*mm, "BANK")

    c.setFillColor(colors.black)

    # 2. Le grand bloc gris structure gauche (Infos Compte / RIB)
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.HexColor("#ECECEC"))
    c.rect(15*mm, 208*mm, 75*mm, 56*mm, fill=True, stroke=True)

    c.setFillColor(colors.black)
    c.setFont(FONT_BLD, 10)
    c.drawCentredString(52.5*mm, 258*mm, ar("كشف بنكي"))
    c.drawCentredString(52.5*mm, 253*mm, "RELEVE DE COMPTE BANCAIRE")
    c.line(15*mm, 251*mm, 90*mm, 251*mm)

    c.setFont(FONT_BLD, 7)
    c.drawString(17*mm, 246*mm, "AGENCE")
    c.drawRightString(88*mm, 246*mm, ar("وكالة"))
    c.setFont(FONT_REG, 7.5)
    c.drawString(32*mm, 246*mm, "CASABLANCA CHEFCHAOUNI")
    c.line(15*mm, 243*mm, 90*mm, 243*mm)

    c.setFont(FONT_BLD, 6.5)
    c.drawString(17*mm, 239*mm, "N° TÉL DE L'AGENCE")
    c.drawRightString(88*mm, 239*mm, ar("رقم هاتف الوكالة"))
    c.setFont(FONT_REG, 7.5)
    c.drawString(42*mm, 239*mm, "0522479779")
    c.line(15*mm, 236*mm, 90*mm, 236*mm)

    c.setFont(FONT_BLD, 7)
    c.drawString(17*mm, 231*mm, "VOTRE CONSEILLER")
    c.drawRightString(88*mm, 231*mm, ar("مستشاركم"))
    c.line(15*mm, 228*mm, 90*mm, 228*mm)

    c.setFont(FONT_BLD, 6.5)
    c.drawString(17*mm, 224*mm, "RELEVE D'IDENTITE BANCAIRE")
    c.drawRightString(88*mm, 224*mm, ar("مقتطف التعريف البنكي"))
    c.line(15*mm, 221*mm, 90*mm, 221*mm)

    # Structure sous-tableau RIB
    c.line(28*mm, 221*mm, 28*mm, 213*mm)
    c.line(41*mm, 221*mm, 41*mm, 213*mm)
    c.line(79*mm, 221*mm, 79*mm, 213*mm)

    c.setFont(FONT_BLD, 6)
    c.drawCentredString(21.5*mm, 217*mm, "BANQUE")
    c.drawCentredString(34.5*mm, 217*mm, "VILLE")
    c.drawCentredString(60*mm, 217*mm, "N° DE COMPTE")
    c.drawCentredString(84.5*mm, 217*mm, "CLE")
    c.line(15*mm, 215*mm, 90*mm, 215*mm)

    c.setFont(FONT_REG, 7)
    c.drawCentredString(21.5*mm, 210.5*mm, "230")
    c.drawCentredString(34.5*mm, 210.5*mm, "330")
    c.drawCentredString(60*mm, 210.5*mm, "5692528211029500")
    c.drawCentredString(84.5*mm, 210.5*mm, "41")
    c.line(15*mm, 208*mm, 90*mm, 208*mm)

    # Devise
    c.rect(15*mm, 199*mm, 75*mm, 7*mm)
    c.line(28*mm, 199*mm, 28*mm, 206*mm)
    c.line(79*mm, 199*mm, 79*mm, 206*mm)
    c.setFont(FONT_BLD, 7)
    c.drawCentredString(21.5*mm, 201.5*mm, "DEVISE")
    c.setFont(FONT_REG, 7.5)
    c.drawCentredString(53.5*mm, 201.5*mm, "DIRHAM MAROCAIN")
    c.setFont(FONT_BLD, 7)
    c.drawCentredString(84.5*mm, 201.5*mm, ar("عملة"))

    # 3. Bloc d'adresse Client (Droite)
    c.setFont(FONT_REG, 9)
    c.drawString(115*mm, 250*mm, "AGENCE DU BASSIN HYDRAULIQUE DU SEBOU")
    c.drawString(115*mm, 244*mm, "ANGLE ABOU EL ALAE EL MAARI ET AHMED CHAOUKI")
    c.drawString(115*mm, 238*mm, "BP 2101 FES")
    c.drawString(115*mm, 232*mm, "MAROC")
    c.drawString(168*mm, 232*mm, "084")

    # 4. Phrase d'accueil bilingue intermédiaire
    c.setFont(FONT_REG, 8.5)
    c.drawString(15*mm, 187*mm, "Nous avons l'honneur de vous communiquer ci-dessous le relevé de votre compte")
    c.drawRightString(195*mm, 187*mm, ar("يشرفنا أن نوافيكم أدناه بكشف حسابكم"))


# -----------------------------
# DESSIN DU TABLEAU DES FLUX (STYLE CIH)
# -----------------------------
def draw_table(c, txs: List[Transaction]):
    x = 15*mm
    y = 180*mm
    w_total = 180*mm

    # Structure de l'en-tête du tableau
    h_header = 10*mm
    c.setFillColor(colors.HexColor("#D3D3D3"))
    c.rect(x, y - h_header, w_total, h_header, fill=True, stroke=True)

    # Découpage des colonnes CIH
    w_dates = 23*mm
    w_lib = 110*mm
    w_deb = 23*mm
    w_cred = 24*mm

    c.setFillColor(colors.black)
    c.setFont(FONT_BLD, 7.5)
    c.drawCentredString(x + w_dates/2, y - 4*mm, "DATES")
    c.setFont(FONT_REG, 6)
    c.drawCentredString(x + 5*mm, y - 8*mm, "OPER")
    c.drawCentredString(x + 17*mm, y - 8*mm, "VALEUR")
    c.line(x + 11.5*mm, y - 5*mm, x + 11.5*mm, y - h_header)

    c.setFont(FONT_BLD, 7.5)
    c.drawString(x + w_dates + 4*mm, y - 6*mm, "OPERATION-REFERENCE")
    c.drawRightString(x + w_dates + w_lib - 4*mm, y - 6*mm, ar("بيان - مرجع"))

    c.drawCentredString(x + w_dates + w_lib + w_deb/2, y - 4*mm, "DEBIT")
    c.setFont(FONT_REG, 6.5)
    c.drawCentredString(x + w_dates + w_lib + w_deb/2, y - 8*mm, ar("مدينة"))

    c.setFont(FONT_BLD, 7.5)
    c.drawCentredString(x + w_dates + w_lib + w_deb + w_cred/2, y - 4*mm, "CREDIT")
    c.setFont(FONT_REG, 6.5)
    c.drawCentredString(x + w_dates + w_lib + w_deb + w_cred/2, y - 8*mm, ar("دائنية"))

    # Lignes verticales intérieures de l'en-tête
    c.line(x + w_dates, y, x + w_dates, y - h_header)
    c.line(x + w_dates + w_lib, y, x + w_dates + w_lib, y - h_header)
    c.line(x + w_dates + w_lib + w_deb, y, x + w_dates + w_lib + w_deb, y - h_header)

    # --- Ligne du Solde de Départ ---
    y_current = y - h_header
    h_row = 6*mm

    c.rect(x, y_current - h_row, w_total, h_row)
    c.setFont(FONT_REG, 7.5)
    c.drawString(x + w_dates + 4*mm, y_current - h_row + 1.8*mm, "SOLDE DEPART AU : 01/07/2023")
    c.drawRightString(x + w_total - 2*mm, y_current - h_row + 1.8*mm, "10,000,000.00")

    # Injection des lignes de transactions
    y_current -= h_row

    for t in txs:
        c.rect(x, y_current - h_row, w_total, h_row)
        c.setFont(FONT_REG, 7)

        # Dates
        c.drawCentredString(x + 5.5*mm, y_current - h_row + 1.8*mm, t.date_op.strftime("%d/%m"))
        c.drawCentredString(x + 17.5*mm, y_current - h_row + 1.8*mm, t.date_val.strftime("%d/%m"))

        # Libellé
        c.drawString(x + w_dates + 4*mm, y_current - h_row + 1.8*mm, t.libelle)

        # Montants
        val_str = f"{t.montant:,.2f}"
        if t.type_flux == "DEBIT":
            c.drawRightString(x + w_dates + w_lib + w_deb - 2*mm, y_current - h_row + 1.8*mm, val_str)
        else:
            c.drawRightString(x + w_total - 2*mm, y_current - h_row + 1.8*mm, val_str)

        y_current -= h_row

    # --- Ligne verticale continue noire (Style CIH) ---
    y_top_table = y
    y_bottom_table = y_current
    c.setLineWidth(0.75)
    c.line(x + w_dates, y_top_table, x + w_dates, y_bottom_table)
    c.line(x + w_dates + w_lib, y_top_table, x + w_dates + w_lib, y_bottom_table)
    c.line(x + w_dates + w_lib + w_deb, y_top_table, x + w_dates + w_lib + w_deb, y_bottom_table)
    c.line(x + 11.5*mm, y_top_table - h_header, x + 11.5*mm, y_bottom_table)

    # --- Totaux et Nouveau Solde (Bas du Tableau CIH) ---
    c.rect(x, y_current - 12*mm, w_total, 12*mm)
    c.line(x + 23*mm, y_current, x + 23*mm, y_current - 12*mm)
    c.line(x + w_dates + w_lib, y_current, x + w_dates + w_lib, y_current - 12*mm)
    c.line(x + w_dates + w_lib + w_deb, y_current, x + w_dates + w_lib + w_deb, y_current - 12*mm)

    c.setFont(FONT_REG, 7)
    c.drawCentredString(x + 11.5*mm, y_current - 5*mm, "PAGE N°")
    c.setFont(FONT_BLD, 7.5)
    c.drawCentredString(x + 11.5*mm, y_current - 10*mm, "001/1")

    c.setFont(FONT_REG, 7.5)
    c.drawString(x + 25*mm, y_current - 5*mm, "TOTAL DES MOUVEMENTS")
    c.drawString(x + 25*mm, y_current - 10*mm, f"NOUVEAU SOLDE AU        {txs[-1].date_op.strftime('%d/%m/%Y')}")

    tot_debit = sum(t.montant for t in txs if t.type_flux == "DEBIT")
    tot_credit = sum(t.montant for t in txs if t.type_flux == "CREDIT")

    c.drawRightString(x + w_dates + w_lib + w_deb - 2*mm, y_current - 5*mm, f"{tot_debit:,.2f}")
    c.drawRightString(x + w_total - 2*mm, y_current - 5*mm, f"{tot_credit:,.2f}")
    c.setFont(FONT_BLD, 8)
    c.drawRightString(x + w_total - 2*mm, y_current - 10*mm, f"{txs[-1].solde:,.2f}")

    # 5. FOOTER LÉGAL CIH (Bordures de contact bilingues)
    y_foot = y_current - 17*mm
    c.setFont(FONT_REG, 7)
    c.drawString(x, y_foot, "Sauf erreur ou omission de notre part")
    c.drawRightString(x + w_total, y_foot, ar("مالم يقع غلط أونسيان من طرفنا"))

    # Boîte de contact double
    y_box = y_foot - 16*mm
    c.setLineWidth(0.5)
    c.rect(x, y_box, w_total, 15*mm)
    c.line(x + 85*mm, y_box, x + 85*mm, y_box + 15*mm)

    c.setFont(FONT_BLD, 7)
    c.drawString(x + 2*mm, y_box + 10*mm, "• Centre Relation Client - CRC, 187 Av Hassan II 20 019 Casablanca")
    c.drawString(x + 2*mm, y_box + 3*mm, "• Médiateur, 187 Hassan II 20 019 Casablanca")

    c.drawString(x + 88*mm, y_box + 10*mm, "Tél. :        05 22 479 479")
    c.drawString(x + 88*mm, y_box + 6.5*mm, "Email :    reclamations-clients@cih.co.ma")
    c.drawString(x + 88*mm, y_box + 3*mm, "Tél. :        05 22 479 210")

    # Bandeau publicitaire CIH
    y_pub = y_box - 12*mm
    c.rect(x, y_pub, w_total, 10*mm)
    c.setFont(FONT_BLD, 7.5)
    c.drawCentredString(x + w_total/2, y_pub + 3.8*mm, "PAYEZ PAR CARTE BANCAIRE CIH BANK ET PROFITEZ JUSQU'À 30% DE RÉDUCTION CHEZ NOS PARTENAIRES")

    # Texte légal d'immatriculation tout en bas
    c.setFont(FONT_REG, 5.2)
    c.setFillColor(colors.HexColor("#444444"))
    legals = "C.I.H siège social : Casablanca-187, Avenue Hassan II - www.cih.co.ma - Tél : 05 22 47 90 00 - Fax : 05 22 47 91 63 S.A. au Capital de 2.832.473.500dh RC : 203 Casa CNSS : 1027805 IF : 01084033, Patente : 34200588, ICE 001542240000068"
    c.drawCentredString(PAGE_W/2, y_pub - 5*mm, legals)


# -----------------------------
# EXECUTION
# -----------------------------
def generate(filename: str, txs: List[Transaction]):
    c = canvas.Canvas(filename, pagesize=A4)
    draw_header(c)
    draw_table(c, txs)
    c.save()


if __name__ == "__main__":
    # Générer des transactions réalistes pour compte CIH
    extracted_txs = extract_all_transactions_from_cih()
    
    print("Nombre de transactions generees:", len(extracted_txs))
    
    # Convertir en objets Transaction
    transactions = []
    for tx in extracted_txs:
        transactions.append(Transaction(**tx))
    
    if not transactions:
        print("Erreur: aucune transaction generee")
        exit(1)

    os.makedirs("data", exist_ok=True)
    generate("data/04_bancaire/releve_cih.pdf", transactions)
    print("✓ Releve CIH genere avec succes: simulators/data/releve_cih.pdf")
    print("Periode: Juillet-Decembre 2023 (6 mois)")
    print("Transactions bancaires realistes CIH BANK")