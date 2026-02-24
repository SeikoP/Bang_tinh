import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * SettingsView — App configuration: UI, TTS, connection, backup, reset.
 */
Item {
    id: settingsRoot

    Component.onCompleted: settingsVM.loadSettings()

    ScrollView {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: 24

            Label {
                text: "Cài đặt"
                font: Theme.typography.titleMedium
                color: Theme.backgroundText
            }

            // ---- UI Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: Theme.surface
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "Giao diện"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Chiều cao dòng (px)"; Layout.fillWidth: true; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        SpinBox {
                            from: 24; to: 64; value: settingsVM.rowHeight
                            onValueModified: settingsVM.rowHeight = value
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Chiều cao widget (px)"; Layout.fillWidth: true; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        SpinBox {
                            from: 200; to: 800; stepSize: 50
                            value: settingsVM.widgetHeight
                            onValueModified: settingsVM.widgetHeight = value
                        }
                    }
                }
            }

            // ---- TTS Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: Theme.surface
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "Text-to-Speech"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Bật TTS"; Layout.fillWidth: true; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        Switch {
                            checked: settingsVM.ttsEnabled
                            Material.accent: Theme.primary
                            onToggled: settingsVM.ttsEnabled = checked
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Giọng đọc"; Layout.fillWidth: true; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        ComboBox {
                            model: ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]
                            currentIndex: settingsVM.ttsVoice === "vi-VN-NamMinhNeural" ? 1 : 0
                            onActivated: settingsVM.ttsVoice = currentText
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Âm lượng"; Layout.fillWidth: true; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        Slider {
                            from: 0; to: 100; stepSize: 5
                            value: settingsVM.ttsVolume !== undefined ? settingsVM.ttsVolume : 80
                            onMoved: settingsVM.ttsVolume = value
                            Layout.preferredWidth: 200
                        }
                        Label {
                            text: Math.round(settingsVM.ttsVolume !== undefined ? settingsVM.ttsVolume : 80) + "%"
                            font: Theme.typography.labelMedium
                            color: Theme.textSecondary
                        }
                    }

                    Button {
                        text: "Thử giọng đọc"
                        flat: true
                        Material.foreground: Theme.primary
                        onClicked: settingsVM.testTts()
                    }
                }
            }

            // ---- Connection Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: Theme.surface
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "Kết nối"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2; columnSpacing: 16; rowSpacing: 10

                        Label { text: "IP máy chủ"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        TextField {
                            Layout.fillWidth: true
                            text: settingsVM.serverIp
                            placeholderText: "192.168.1.x"
                            onEditingFinished: settingsVM.serverIp = text
                        }

                        Label { text: "Cổng"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        TextField {
                            Layout.fillWidth: true
                            text: settingsVM.serverPort
                            placeholderText: "5000"
                            inputMethodHints: Qt.ImhDigitsOnly
                            onEditingFinished: settingsVM.serverPort = text
                        }

                        Label { text: "Số máy"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
                        SpinBox {
                            from: 1; to: 99
                            value: settingsVM.machineCount
                            onValueModified: settingsVM.machineCount = value
                        }
                    }

                    // QR Code
                    Rectangle {
                        Layout.alignment: Qt.AlignHCenter
                        width: 180; height: 180
                        radius: Theme.radiusLg
                        border.width: 1; border.color: Theme.outline
                        color: Theme.backgroundSecondary

                        Image {
                            anchors.fill: parent
                            anchors.margins: 8
                            visible: (settingsVM.qrCodeData || "") !== ""
                            source: settingsVM.qrCodeData || ""
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: (settingsVM.qrCodeData || "") === ""
                            text: "Chưa tạo QR"
                            font: Theme.typography.labelMedium
                            color: Theme.textDisabled
                        }
                    }
                }
            }

            // ---- Backup Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: Theme.surface
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "Sao lưu / Khôi phục"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }

                    // Auto-backup status
                    RowLayout {
                        Layout.fillWidth: true; spacing: 8
                        Rectangle {
                            width: 8; height: 8; radius: 4
                            color: settingsVM.autoBackupEnabled ? Theme.success : Theme.textDisabled
                        }
                        Label {
                            text: settingsVM.autoBackupEnabled ? "Tự động sao lưu: Bật" : "Tự động sao lưu: Tắt"
                            font: Theme.typography.labelMedium
                            color: Theme.surfaceVariantText
                        }
                        Label {
                            visible: (settingsVM.lastBackupTime || "") !== ""
                            text: "Lần cuối: " + (settingsVM.lastBackupTime || "")
                            font: Theme.typography.labelSmall
                            color: Theme.textDisabled
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12

                        Button {
                            text: "Tạo bản sao lưu"
                            Material.background: Theme.primary
                            Material.foreground: Theme.surface
                            onClicked: settingsVM.createBackup()
                        }

                        Button {
                            text: "Khôi phục"
                            Material.background: Theme.error
                            Material.foreground: Theme.surface
                            onClicked: {
                                backupListModel.clear()
                                var list = settingsVM.getBackupList()
                                for (var i = 0; i < list.length; i++) {
                                    backupListModel.append({"name": list[i]})
                                }
                                restoreDialog.open()
                            }
                        }
                    }
                }
            }

            // ---- Reset Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: Theme.surface
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "Nâng cao"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }

                    Button {
                        text: "Reset mặc định"
                        flat: true
                        Material.foreground: Theme.error
                        onClicked: resetConfirmDialog.open()
                    }
                }
            }

            Item { Layout.fillHeight: true } // spacer
        }
    }

    // Restore backup dialog
    Dialog {
        id: restoreDialog
        title: "Chọn bản sao lưu"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Cancel
        width: 400

        ListModel { id: backupListModel }

        ListView {
            width: parent.width
            height: 300
            model: backupListModel
            clip: true

            delegate: ItemDelegate {
                width: parent ? parent.width : 0
                text: model.name
                onClicked: {
                    settingsVM.restoreBackup(model.name)
                    restoreDialog.close()
                }
            }
        }
    }

    // Reset confirm dialog
    ConfirmDialog {
        id: resetConfirmDialog
        title: "Reset cài đặt"
        message: "Khôi phục tất cả cài đặt về mặc định? Thao tác này không thể hoàn tác."
        confirmText: "Reset"
        onConfirmed: settingsVM.resetDefaults()
    }

    Connections {
        target: settingsVM
        function onBackupCreated() { globalToast.show("Đã tạo bản sao lưu", "success") }
        function onBackupRestored() { globalToast.show("Đã khôi phục dữ liệu", "success") }
        function onSettingsReset() { globalToast.show("Đã reset cài đặt", "info") }
    }
}
