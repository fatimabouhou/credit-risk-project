import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# -----------------------------
# CONFIGURATION ET STYLES
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGO_DIR = os.path.join(BASE_DIR, "logos")

os.makedirs(DATA_DIR, exist_ok=True)

ORANGE_ATTIJARI = colors.HexColor("#FF5F00")
DARK_GREY = colors.HexColor("#333333")
LIGHT_GREY = colors.HexColor("#F5F5F5")

styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    'DocTitle',
    fontName='Helvetica-Bold',
    fontSize=14,
    textColor=ORANGE_ATTIJARI,
    alignment=1, # Center
    spaceAfter=15
)

style_client = ParagraphStyle(
    'ClientInfo',
    fontName='Helvetica-Bold',
    fontSize=11,
    textColor=DARK_GREY,
    alignment=1,
    spaceAfter=5
)

style_date = ParagraphStyle(
    'DateInfo',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.gray,
    alignment=1,
    spaceAfter=20
)

style_loan_title = ParagraphStyle(
    'LoanTitle',
    fontName='Helvetica-Bold',
    fontSize=12,
    textColor=colors.white,
    backColor=DARK_GREY,
    alignment=0,
    spaceBefore=15,
    spaceAfter=5,
    leftIndent=5,
    rightIndent=5,
    borderPadding=4
)

style_loan_params = ParagraphStyle(
    'LoanParams',
    fontName='Helvetica',
    fontSize=9,
    textColor=DARK_GREY,
    spaceAfter=10,
    leading=12
)

style_loan_footer = ParagraphStyle(
    'LoanFooter',
    fontName='Helvetica-Oblique',
    fontSize=9,
    textColor=colors.gray,
    alignment=2, # Right
    spaceBefore=5,
    spaceAfter=15
)

# -----------------------------
# DONNÉES DES CRÉDITS
# -----------------------------
def get_loan_1_data():
    return [
        ["DATE", "PRINCIPAL", "INTERET", "TOTALITE", "SOLDE"],
        ["01/07/2023", "538,820", "348,806", "887,626", "104,102,857"],
        ["01/08/2023", "540,616", "347,010", "887,626", "103,562,241"],
        ["01/09/2023", "542,418", "345,207", "887,626", "103,019,823"],
        ["01/10/2023", "544,226", "343,399", "887,626", "102,475,597"],
        ["01/11/2023", "546,040", "341,585", "887,626", "101,929,556"],
        ["01/12/2023", "547,860", "339,765", "887,626", "101,381,696"],
        ["01/01/2024", "549,687", "337,939", "887,626", "100,832,010"],
        ["01/02/2024", "551,519", "336,107", "887,626", "100,280,491"],
        ["01/03/2024", "553,357", "334,268", "887,626", "99,727,134"],
        ["01/04/2024", "555,202", "332,424", "887,626", "99,171,932"],
        ["01/05/2024", "557,052", "330,573", "887,626", "98,614,879"],
        ["01/06/2024", "558,909", "328,716", "887,626", "98,055,970"]
    ]

def get_loan_2_data():
    return [
        ["DATE", "PRINCIPAL", "INTERET", "TOTALITE", "SOLDE"],
        ["01/07/2023", "280,566", "102,588", "383,154", "34,892,584"],
        ["01/08/2023", "281,384", "101,770", "383,154", "34,611,200"],
        ["01/09/2023", "282,205", "100,949", "383,154", "34,328,995"],
        ["01/10/2023", "283,028", "100,126", "383,154", "34,045,967"],
        ["01/11/2023", "283,853", "99,301", "383,154", "33,762,114"],
        ["01/12/2023", "284,681", "98,473", "383,154", "33,477,432"],
        ["01/01/2024", "285,512", "97,643", "383,154", "33,191,921"],
        ["01/02/2024", "286,344", "96,810", "383,154", "32,905,576"],
        ["01/03/2024", "287,180", "95,975", "383,154", "32,618,397"],
        ["01/04/2024", "288,017", "95,137", "383,154", "32,330,380"],
        ["01/05/2024", "288,857", "94,297", "383,154", "32,041,522"],
        ["01/06/2024", "289,700", "93,454", "383,154", "31,751,823"]
    ]

def create_table(data):
    # Création du tableau avec largeurs de colonnes ajustées
    t = Table(data, colWidths=[30*mm, 35*mm, 35*mm, 35*mm, 40*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE_ATTIJARI),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),

        # Style des données
        ('ALIGN', (0, 1), (0, -1), 'CENTER'), # Dates centrées
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'), # Montants à droite
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]) # Lignes alternées
    ]))
    return t

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_amortization_schedule(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # Header : Logo de la banque
    logo_path = os.path.join(LOGO_DIR, "attijari_logo.png")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=42*mm, height=15*mm)
        img.hAlign = 'LEFT'
        story.append(img)
    else:
        # Fallback si le logo n'est pas trouvé
        story.append(Paragraph("<b>التجاري وفا بنك<br/>Attijariwafa bank</b>", ParagraphStyle('Bank', fontName='Helvetica', fontSize=12, alignment=0, textColor=DARK_GREY)))

    story.append(Spacer(1, 15))

    # Titre et Client
    story.append(Paragraph("TABLEAU D'AMORTISSEMENT DES CREDITS", style_title))
    story.append(Paragraph("AGENCE DU BASSIN HYDRAULIQUE DU SEBOU (ABHS)", style_client))
    story.append(Paragraph("Situation au 01 juillet 2023", style_date))
    story.append(Spacer(1, 10))

    # --- CREDIT 1 ---
    story.append(Paragraph("CREDIT BARRAGE - Phase Construction", style_loan_title))
    params1 = "<b>Capital initial:</b> 120,000,000 DH | <b>Taux:</b> 4.0% p.a. | <b>Durée:</b> 15 ans<br/>"
    params1 += "<b>Capital restant au 01/07/2023:</b> 104,641,677 DH | <b>Mensualité:</b> 887,626 DH"
    story.append(Paragraph(params1, style_loan_params))

    story.append(create_table(get_loan_1_data()))
    story.append(Paragraph("Mois remboursés: 30/180 | Mois restants: 150", style_loan_footer))

    # --- CREDIT 2 ---
    story.append(Paragraph("CREDIT IMMOBILIER - Equipements", style_loan_title))
    params2 = "<b>Capital initial:</b> 45,000,000 DH | <b>Taux:</b> 3.5% p.a. | <b>Durée:</b> 12 ans<br/>"
    params2 += "<b>Capital restant au 01/07/2023:</b> 35,173,150 DH | <b>Mensualité:</b> 383,154 DH"
    story.append(Paragraph(params2, style_loan_params))

    story.append(create_table(get_loan_2_data()))
    story.append(Paragraph("Mois remboursés: 37/144 | Mois restants: 107", style_loan_footer))

    # --- FOOTER LÉGAL ---
    story.append(Spacer(1, 20))
    story.append(Paragraph("Attijariwafa Bank - Document confidentiel - Situation au 01/07/2023", ParagraphStyle('Legal', fontName='Helvetica', fontSize=8, textColor=colors.gray, alignment=1)))

    doc.build(story)
    print(f"✅ Tableau d'amortissement avec logo généré avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "amortissement_credits.pdf")
    generate_amortization_schedule(output_path)