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

# Couleurs pour le design
BLUE_CORP = colors.HexColor("#004B87")
LIGHT_GREY = colors.HexColor("#F9F9F9")

styles = getSampleStyleSheet()

style_expediteur = ParagraphStyle(
    'Expediteur',
    fontName='Helvetica-Bold',
    fontSize=10,
    textColor=BLUE_CORP,
    leading=12 # Réduit
)

style_destinataire = ParagraphStyle(
    'Destinataire',
    fontName='Helvetica-Bold',
    fontSize=10,
    alignment=2, # Droite
    leading=12 # Réduit
)

style_objet = ParagraphStyle(
    'Objet',
    fontName='Helvetica-Bold',
    fontSize=11,
    spaceBefore=5,
    spaceAfter=10
)

style_body = ParagraphStyle(
    'BodyText',
    fontName='Helvetica',
    fontSize=10, # Passé à 10 pour gagner de la place
    leading=14,  # Réduit
    alignment=4, # Justifié
    spaceAfter=8
)

style_table_key = ParagraphStyle(
    'TableKey',
    fontName='Helvetica-Bold',
    fontSize=10,
    textColor=colors.black,
    leading=12
)

style_table_value = ParagraphStyle(
    'TableValue',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    leading=13
)

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_demande_credit(filename):
    # Marges minimales pour forcer la page unique
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    story = []

    # 1. En-tête : Expéditeur (Gauche) et Date (Droite)
    header_data = [
        [
            Paragraph("<b>ABHS SARL</b><br/>Gérant : Mohamed El Amrani<br/>ICE : 001234567890123<br/>RC : 12345 Kénitra<br/>IF : 12345678", style_expediteur),
            Paragraph("Kénitra, le 15 Décembre 2023", style_destinataire)
        ]
    ]
    t_header = Table(header_data, colWidths=[100*mm, 80*mm])
    t_header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(t_header)

    story.append(Spacer(1, 10*mm))

    # 2. Destinataire
    story.append(Paragraph("À l'attention de la Direction du Centre d'Affaires<br/>Attijariwafa Bank / CIH Bank", style_destinataire))
    story.append(Spacer(1, 8*mm))

    # 3. Objet
    story.append(Paragraph("<u>Objet</u> : Demande de financement (Acquisition de nouveaux équipements)", style_objet))

    # 4. Corps de la lettre (Introduction)
    story.append(Paragraph("Monsieur le Directeur,", style_body))

    intro_text = """
    Dans le cadre du développement de notre activité de commerce de matériaux de construction 
    (créée le 12/04/2018), nous avons l'honneur de vous solliciter par la présente pour l'octroi 
    d'un financement bancaire visant à soutenir notre plan d'investissement pour l'année 2024.
    <br/><br/>
    Notre entreprise ayant réalisé un chiffre d'affaires de <b>18 700 000 MAD en 2023</b> et affichant 
    une structure financière saine, nous souhaiterions mettre en place ce concours aux conditions suivantes :
    """
    story.append(Paragraph(intro_text, style_body))
    story.append(Spacer(1, 3*mm))

    # 5. Les caractéristiques du crédit
    credit_details = [
        [Paragraph("Montant demandé :", style_table_key), Paragraph("<b>2 500 000,00 MAD</b>", style_table_value)],
        [Paragraph("Durée du crédit :", style_table_key), Paragraph("<b>60 mois</b> (dont 6 mois de différé)", style_table_value)],
        [Paragraph("Apport personnel :", style_table_key), Paragraph("<b>500 000,00 MAD</b>", style_table_value)],
        [Paragraph("Objet du financement :", style_table_key), Paragraph("Acquisition de nouveaux équipements.", style_table_value)],
        [Paragraph("Garanties proposées :", style_table_key), Paragraph("&bull; Hypothèque sur un local commercial<br/>&bull; Nantissement du matériel<br/>&bull; Caution solidaire du gérant", style_table_value)]
    ]

    t_details = Table(credit_details, colWidths=[55*mm, 125*mm])
    t_details.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6), # Padding réduit
        ('TOPPADDING', (0, 0), (-1, -1), 6),    # Padding réduit
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY)
    ]))
    story.append(t_details)
    story.append(Spacer(1, 5*mm))

    # 6. Conclusion
    conclusion_text = """
    Vous trouverez ci-joint l'ensemble du dossier juridique et financier (bilans, liasses fiscales, 
    attestations de régularité et relevés bancaires) nécessaires à l'étude de notre requête.
    <br/><br/>
    Nous restons à votre entière disposition pour tout complément d'information et vous prions 
    d'agréer, Monsieur le Directeur, l'expression de nos salutations distinguées.
    """
    story.append(Paragraph(conclusion_text, style_body))
    story.append(Spacer(1, 8*mm))

    # 7. Signature
    story.append(Paragraph("<b>Mohamed El Amrani</b><br/><i>Gérant (Cachet et Signature)</i>", style_destinataire))

    doc.build(story)
    print(f"✅ Demande de crédit ABHS SARL générée sur une seule page avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "demande_credit.pdf")
    generate_demande_credit(output_path)