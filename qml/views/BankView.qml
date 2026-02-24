import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * BankView — Bank transaction notifications with tabs.
 */
Item {
    id: bankViewRoot

    Component.onCompleted: bankVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Tab Bar
        TabBar {
            id: bankTabBar
            Layout.fillWidth: true
            Material.accent: Theme.primary

            TabButton {
                text: "Giao dịch"
                font: Theme.typography.labelLarge
                width: implicitWidth
            }

            TabButton {
                text: "Logs"
                font: Theme.typography.labelLarge
                width: implicitWidth
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: bankTabBar.currentIndex

            // ━━━ TAB 0: Transactions ━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingSm

                    // Header
                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            text: "Giao dịch Ngân hàng"
                            font: Theme.typography.titleMedium
                            color: Theme.backgroundText
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
                            Material.foreground: Theme.error
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
                            radius: Theme.radiusLg
                            color: bankItemMouse.containsMouse ? Theme.surfaceVariant : Theme.surface
                            border.width: 1
                            border.color: Theme.divider

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Theme.spacingMd
                                anchors.rightMargin: Theme.spacingMd
                                spacing: Theme.spacingSm

                                // Source indicator
                                Rectangle {
                                    width: 44; height: 44
                                    radius: Theme.radiusMd
                                    color: {
                                        var src = model.source || ""
                                        if (src.indexOf("MoMo") >= 0) return Theme.withAlpha(Theme.secondary, 0.1)
                                        if (src.indexOf("Vietin") >= 0) return Theme.withAlpha(Theme.info, 0.1)
                                        return Theme.withAlpha(Theme.primary, 0.1)
                                    }

                                    Label {
                                        anchors.centerIn: parent
                                        text: {
                                            var src = model.source || ""
                                            if (src.indexOf("MoMo") >= 0) return "M"
                                            if (src.indexOf("Vietin") >= 0) return "V"
                                            return "B"
                                        }
                                        font.pixelSize: 18
                                        font.weight: Font.Bold
                                        color: {
                                            var src = model.source || ""
                                            if (src.indexOf("MoMo") >= 0) return Theme.secondary
                                            if (src.indexOf("Vietin") >= 0) return Theme.info
                                            return Theme.primary
                                        }
                                    }
                                }

                                // Transaction info
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Label {
                                        text: model.senderName || "Không rõ"
                                        font: Theme.typography.labelLarge
                                        color: Theme.backgroundText
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        text: model.content || ""
                                        font: Theme.typography.bodySmall
                                        color: Theme.surfaceVariantText
                                        elide: Text.ElideRight
                                        maximumLineCount: 1
                                    }

                                    RowLayout {
                                        spacing: Theme.spacingSm
                                        Label {
                                            text: model.source || ""
                                            font: Theme.typography.labelSmall; color: Theme.textDisabled
                                        }
                                        Label {
                                            text: model.timeStr || ""
                                            font: Theme.typography.labelSmall; color: Theme.textDisabled
                                        }
                                    }
                                }

                                // Amount
                                Label {
                                    text: model.amount || "0"
                                    font: Theme.typography.titleMedium
                                    color: Theme.primary
                                }

                                // Delete
                                RoundButton {
                                    text: "Xóa"
                                    width: 48; height: 32
                                    flat: true
                                    font: Theme.typography.labelSmall
                                    Material.foreground: Theme.error
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
                            font: Theme.typography.bodyLarge
                            color: Theme.textDisabled
                        }
                    }
                }
            }

            // ━━━ TAB 1: Raw Logs ━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingSm

                    Label {
                        text: "Nhật ký hệ thống"
                        font: Theme.typography.titleMedium
                        color: Theme.backgroundText
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.radiusMd
                        color: Theme.backgroundSecondary
                        border.width: 1
                        border.color: Theme.outline

                        ScrollView {
                            anchors.fill: parent
                            anchors.margins: Theme.spacingSm

                            Label {
                                width: parent.width
                                text: bankVM.rawLogs || "Chưa có log nào"
                                font: Qt.font({ family: "Consolas", pixelSize: 12 })
                                color: Theme.surfaceVariantText
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }
    }

    ConfirmDialog { id: clearConfirm }
}
