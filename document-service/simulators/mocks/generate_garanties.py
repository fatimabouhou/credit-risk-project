import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# -----------------------------
# CONFIGURATION ET STYLES
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

BLUE_CORP = colors.HexColor("#004B87")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
LIGHT_GREY = colors.HexColor("#F9F9F9")

styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    'DocTitle',
    fontName='Helvetica-Bold',
    fontSize=14,
    textColor=BLUE_CORP,
    alignment=1, # Center
    spaceBefore=20,
    spaceAfter=20
)

style_section = ParagraphStyle(
    'SectionTitle',
    fontName='Helvetica-Bold',
    fontSize=12,
    textColor=colors.black,
    spaceBefore=15,
    spaceAfter=10
)

style_table_key = ParagraphStyle(
    'TableKey',
    fontName='Helvetica-Bold',
    fontSize=10,
    textColor=colors.black,
    leading=14
)

style_table_value = ParagraphStyle(
    'TableValue',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    leading=14
)

style_header = ParagraphStyle(
    'Header',
    fontName='Helvetica-Oblique',
    fontSize=10,
    textColor=colors.grey,
    alignment=2,
    spaceAfter=15
)

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_garanties(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    story = []

    # Référence au dossier
    story.append(Paragraph("Dossier de financement : ABHS SARL (ICE : 001234567890123)", style_header))

    # Titre du document
    story.append(Paragraph("ANNEXE : DÉTAIL DES GARANTIES PROPOSÉES", style_title))

    # ---------------------------------------------------------
    # 1. HYPOTHÈQUE
    # ---------------------------------------------------------
    story.append(Paragraph("1. Hypothèque en premier rang", style_section))

    data_hypo = [
        [Paragraph("Nature du bien :", style_table_key), Paragraph("Local industriel", style_table_value)],
        [Paragraph("Titre Foncier (TF) :", style_table_key), Paragraph("14589/13", style_table_value)],
        [Paragraph("Adresse :", style_table_key), Paragraph("Zone Industrielle Bir Rami, Lot n° 45, Kénitra", style_table_value)],
        [Paragraph("Valeur estimée :", style_table_key), Paragraph("<b>4 300 000,00 MAD</b>", style_table_value)],
        [Paragraph("Expert immobilier :", style_table_key), Paragraph("Cabinet d'Expertise Immobilière El Fassi (Agréé)", style_table_value)],
        [Paragraph("Date d'estimation :", style_table_key), Paragraph("05/12/2023", style_table_value)]
    ]

    t_hypo = Table(data_hypo, colWidths=[55*mm, 115*mm])
    t_hypo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE), # Colonne 1 en bleu clair
        ('BACKGROUND', (1, 0), (1, -1), colors.white)
    ]))
    story.append(t_hypo)
    story.append(Spacer(1, 10*mm))

    # ---------------------------------------------------------
    # 2. NANTISSEMENT
    # ---------------------------------------------------------
    story.append(Paragraph("2. Nantissement sur matériel", style_section))

    data_nantissement = [
        [Paragraph("Nature du bien :", style_table_key), Paragraph("Machine de découpe CNC haute précision", style_table_value)],
        [Paragraph("État :", style_table_key), Paragraph("Neuf (Objet partiel du financement)", style_table_value)],
        [Paragraph("Valeur d'acquisition :", style_table_key), Paragraph("<b>900 000,00 MAD</b>", style_table_value)]
    ]

    t_nant = Table(data_nantissement, colWidths=[55*mm, 115*mm])
    t_nant.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
        ('BACKGROUND', (1, 0), (1, -1), colors.white)
    ]))
    story.append(t_nant)
    story.append(Spacer(1, 10*mm))

    # ---------------------------------------------------------
    # 3. CAUTION PERSONNELLE
    # ---------------------------------------------------------
    story.append(Paragraph("3. Caution solidaire", style_section))

    data_caution = [
        [Paragraph("Identité de la caution :", style_table_key), Paragraph("Monsieur Mohamed El Amrani", style_table_value)],
        [Paragraph("Qualité :", style_table_key), Paragraph("Gérant et Associé principal (80%)", style_table_value)],
        [Paragraph("Engagement :", style_table_key), Paragraph("Couverture à hauteur de 100% du montant du crédit", style_table_value)]
    ]

    t_caut = Table(data_caution, colWidths=[55*mm, 115*mm])
    t_caut.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
        ('BACKGROUND', (1, 0), (1, -1), colors.white)
    ]))
    story.append(t_caut)

    doc.build(story)
    print(f"✅ Annexe des garanties générée avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "annexe_garanties.pdf")
    generate_garanties(output_path)