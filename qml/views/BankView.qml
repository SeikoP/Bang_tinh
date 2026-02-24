import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * BankView — Bank transaction notifications.
 */
Item {
    id: bankViewRoot

    Component.onCompleted: bankVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "💰 Giao dịch Ngân hàng"
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#1F2937"
            }

            Item { Layout.fillWidth: true }

            // Source filter
            ComboBox {
                id: sourceFilter
                Layout.preferredWidth: 180
                model: ["Tất cả"].concat(bankVM.getAvailableSources())
                onCurrentTextChanged: {
                    bankVM.sourceFilter = currentIndex === 0 ? "" : currentText
                }
            }

            Button {
                text: "Xóa tất cả"
                flat: true
                Material.foreground: "#DC2626"
                onClicked: clearConfirm.show(
                    "Xóa tất cả?",
                    "Tất cả giao dịch ngân hàng sẽ bị xóa.",
                    function() { bankVM.clearAll() }
                )
            }
        }

        // Transaction list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: bankVM.notifications
            spacing: 6

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 72
                radius: 12
                color: bankItemMouse.containsMouse ? "#F3F4F6" : "white"
                border.width: 1
                border.color: "#F3F4F6"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 12

                    // Source icon
                    Rectangle {
                        width: 44; height: 44
                        radius: 10
                        color: {
                            var src = model.source || ""
                            if (src.indexOf("MoMo") >= 0) return "#ffe0f0"
                            if (src.indexOf("Vietin") >= 0) return "#dbeafe"
                            return "#d1fae5"
                        }

                        Label {
                            anchors.centerIn: parent
                            text: {
                                var src = model.source || ""
                                if (src.indexOf("MoMo") >= 0) return "📱"
                                if (src.indexOf("Vietin") >= 0) return "🏦"
                                return "💳"
                            }
                            font.pixelSize: 20
                        }
                    }

                    // Transaction info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.senderName || "Không rõ"
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            color: "#1F2937"
                        }

                        Label {
                            Layout.fillWidth: true
                            text: model.content || ""
                            font.pixelSize: 12
                            color: "#6B7280"
                            elide: Text.ElideRight
                            maximumLineCount: 1
                        }

                        RowLayout {
                            spacing: 12
                            Label {
                                text: model.source || ""
                                font.pixelSize: 11; color: "#9CA3AF"
                            }
                            Label {
                                text: model.timeStr || ""
                                font.pixelSize: 11; color: "#9CA3AF"
                            }
                        }
                    }

                    // Amount
                    Label {
                        text: model.amount || "0"
                        font.pixelSize: 18
                        font.weight: Font.Bold
                        color: "#10B981"
                    }

                    // Delete
                    RoundButton {
                        text: "🗑️"
                        width: 32; height: 32
                        flat: true
                        onClicked: bankVM.deleteNotification(model.notificationId)
                    }
                }

                MouseArea {
                    id: bankItemMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    propagateComposedEvents: true
                    onPressed: function(mouse) { mouse.accepted = false }
                }
            }

            // Empty state
            Label {
                anchors.centerIn: parent
                visible: bankVM.notifications.count === 0
                text: "Chưa có giao dịch nào"
                font.pixelSize: 16
                color: "#9CA3AF"
            }
        }
    }

    ConfirmDialog { id: clearConfirm }
}
