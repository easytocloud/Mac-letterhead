from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from PIL import Image
import os

# Get paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
logo_path = os.path.join(project_root, "letterhead_pdf/resources/icon.png")
output_path = os.path.join(script_dir, "test-letterhead.pdf")

# Create the PDF
c = canvas.Canvas(output_path, pagesize=A4)
width, height = A4

# Load and prepare the logo
img = Image.open(logo_path)
aspect = img.width / img.height

# Page 1 - Large logo + footer
logo_height = 1.5 * inch
logo_width = logo_height * aspect
c.drawImage(logo_path, 0.75 * inch, height - 2.25 * inch, width=logo_width, height=logo_height)

# Add footer
c.setFont("Helvetica", 10)
c.drawString(0.75 * inch, 1 * inch, "Letterhead Technologies, Inc.")
c.drawString(0.75 * inch, 0.75 * inch, "123 Innovation Way, Silicon Valley, CA 94025 | (555) 123-4567 | www.letterheadtech.com")
c.showPage()

# Page 2 - Small logo top left
logo_height = 0.75 * inch
logo_width = logo_height * aspect
c.drawImage(logo_path, 0.75 * inch, height - 1.5 * inch, width=logo_width, height=logo_height)
c.showPage()

# Page 3 - Small logo top right
c.drawImage(logo_path, width - logo_width - 0.75 * inch, height - 1.5 * inch, width=logo_width, height=logo_height)
c.showPage()

# Save the PDF
c.save()
