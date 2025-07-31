import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QHBoxLayout, QSpinBox, QComboBox
)
from sfz_gen import generate_sfz, config, analyze_key_mapping

class SFZGeneratorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SFZ Generator")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Sample path selector
        self.sample_path_label = QLabel("Sample Path:")
        self.sample_path_input = QLineEdit(config['sample_path'])
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_samples)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.sample_path_input)
        path_layout.addWidget(self.browse_button)

        # Release time
        self.release_label = QLabel("Release Time (s):")
        self.release_input = QLineEdit(str(config['release_time']))

        # Enable dynamics
        self.dynamics_checkbox = QCheckBox("Enable Dynamics Curve")
        self.dynamics_checkbox.setChecked(config['enable_dynamics_curve'])

        # Velocity layers
        self.layers_label = QLabel("Velocity Layer Count:")
        self.layers_spinbox = QSpinBox()
        self.layers_spinbox.setRange(1, 128)
        self.layers_spinbox.setValue(config['layer_count'])

        # Curve type
        self.curve_label = QLabel("Velocity Curve Type:")
        self.curve_combo = QComboBox()
        self.curve_combo.addItems(["linear", "logarithmic", "exponential"])
        self.curve_combo.setCurrentText(config['velocity_curve'])

        # Generate button
        self.generate_button = QPushButton("Generate SFZ")
        self.generate_button.clicked.connect(self.generate_sfz_file)

        layout.addWidget(self.sample_path_label)
        layout.addLayout(path_layout)
        layout.addWidget(self.release_label)
        layout.addWidget(self.release_input)
        layout.addWidget(self.dynamics_checkbox)
        layout.addWidget(self.layers_label)
        layout.addWidget(self.layers_spinbox)
        layout.addWidget(self.curve_label)
        layout.addWidget(self.curve_combo)
        layout.addWidget(self.generate_button)

        self.setLayout(layout)

    def browse_samples(self):
        path = QFileDialog.getExistingDirectory(self, "Select Sample Directory")
        if path:
            self.sample_path_input.setText(path)

    def generate_sfz_file(self):
        # Apply modified values
        try:
            config['sample_path'] = self.sample_path_input.text()
            config['release_time'] = float(self.release_input.text())
            config['enable_dynamics_curve'] = self.dynamics_checkbox.isChecked()
            config['layer_count'] = self.layers_spinbox.value()
            config['velocity_curve'] = self.curve_combo.currentText()

            sfz = generate_sfz(**config)

            with open("Piano.sfz", "w") as f:
                f.write(sfz)

            analyze_key_mapping(
                generate_sfz.key_to_sample_map,
                generate_sfz.existing_sample_formats,
                config['key_range'][0],
                config['key_range'][1],
                config['sample_range'][0],
                config['sample_range'][1]
            )

            QMessageBox.information(self, "Success", "SFZ file 'Piano.sfz' generated successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SFZGeneratorUI()
    window.show()
    sys.exit(app.exec_())
