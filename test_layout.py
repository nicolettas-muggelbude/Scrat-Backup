  import sys
  sys.path.insert(0, 'src')

  from gui.wizard_v2 import SetupWizardV2
  from PySide6.QtWidgets import QApplication

  app = QApplication(sys.argv)
  wizard = SetupWizardV2()

  # Debug: Prüfe Grid-Layout
  dest_page = wizard.page(1)
  print(f"DestinationPage gefunden: {dest_page is not None}")

  wizard.show()
  sys.exit(app.exec())
  EOF
