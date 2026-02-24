import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * SettingsView — App configuration: UI, TTS, connection, backup.
 */
Item {
    id: settingsRoot

    Component.onCompleted: settingsVM.loadSettings()

    ScrollView {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: 24

            Label {
                text: "⚙️ Cài đặt"
                font.pixelSize: 18; font.weight: Font.Medium
                color: "#1F2937"
            }

            // ---- UI Section ----
            settingsCard("🎨 Giao diện") {
                RowLayout {
                    Layout.fillWidth: true; spacing: 12
                    Label { text: "Chiều cao dòng (px)"; Layout.fillWidth: true; color: "#374151" }
                    SpinBox {
                        from: 24; to: 64; value: settingsVM.rowHeight
                        onValueModified: settingsVM.rowHeight = value
                    }
                }

                RowLayout {
                    Layout.fillWidth: true; spacing: 12
                    Label { text: "Chiều cao widget (px)"; Layout.fillWidth: true; color: "#374151" }
                    SpinBox {
                        from: 200; to: 800; stepSize: 50
                        value: settingsVM.widgetHeight
                        onValueModified: settingsVM.widgetHeight = value
                    }
                }
            }

            // ---- TTS Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: "white"
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "🔊 Text-to-Speech"
                        font.pixelSize: 15; font.weight: Font.Medium
                        color: "#1F2937"
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Bật TTS"; Layout.fillWidth: true; color: "#374151" }
                        Switch {
                            checked: settingsVM.ttsEnabled
                            onToggled: settingsVM.ttsEnabled = checked
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12
                        Label { text: "Giọng đọc"; Layout.fillWidth: true; color: "#374151" }
                        ComboBox {
                            model: ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"]
                            currentIndex: settingsVM.ttsVoice === "vi-VN-NamMinhNeural" ? 1 : 0
                            onActivated: settingsVM.ttsVoice = currentText
                        }
                    }
                }
            }

            // ---- Connection Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: "white"
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "📡 Kết nối"
                        font.pixelSize: 15; font.weight: Font.Medium
                        color: "#1F2937"
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: 2; columnSpacing: 16; rowSpacing: 10

                        Label { text: "IP máy chủ"; color: "#374151" }
                        TextField {
                            Layout.fillWidth: true
                            text: settingsVM.serverIp
                            placeholderText: "192.168.1.x"
                            onEditingFinished: settingsVM.serverIp = text
                        }

                        Label { text: "Cổng"; color: "#374151" }
                        TextField {
                            Layout.fillWidth: true
                            text: settingsVM.serverPort
                            placeholderText: "5000"
                            inputMethodHints: Qt.ImhDigitsOnly
                            onEditingFinished: settingsVM.serverPort = text
                        }

                        Label { text: "Số máy"; color: "#374151" }
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
                        radius: 12; border.width: 1; border.color: "#E5E7EB"
                        color: "#FAFAFA"

                        Label {
                            anchors.centerIn: parent
                            text: settingsVM.qrCodeData ? "📱 QR" : "Chưa tạo QR"
                            font.pixelSize: 13; color: "#9CA3AF"
                        }
                    }
                }
            }

            // ---- Backup Section ----
            Pane {
                Layout.fillWidth: true
                Material.elevation: 1
                Material.background: "white"
                padding: 20

                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label {
                        text: "💾 Sao lưu / Khôi phục"
                        font.pixelSize: 15; font.weight: Font.Medium
                        color: "#1F2937"
                    }

                    RowLayout {
                        Layout.fillWidth: true; spacing: 12

                        Button {
                            text: "Tạo bản sao lưu"
                            Material.background: "#10b981"
                            Material.foreground: "white"
                            onClicked: settingsVM.createBackup()
                        }

                        Button {
                            text: "Khôi phục"
                            Material.background: "#ef4444"
                            Material.foreground: "white"
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

            Item { Layout.fillHeight: true } // spacer
        }
    }

    // inline component for settings card (UI section)
    component settingsCard: Pane {
        property string sectionTitle
        default property alias contentChildren: innerCol.children

        Layout.fillWidth: true
        Material.elevation: 1
        Material.background: "white"
        padding: 20

        ColumnLayout {
            id: innerCol
            width: parent.width
            spacing: 12

            Label {
                text: sectionTitle
                font.pixelSize: 15; font.weight: Font.Medium
                color: "#1F2937"
            }
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
}
