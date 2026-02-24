import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * HistoryView — Session history list with detail dialog.
 */
Item {
    id: historyViewRoot

    Component.onCompleted: historyVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingSm

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Lịch sử Ca"
                font: Theme.typography.titleMedium
                color: Theme.backgroundText
            }

            Item { Layout.fillWidth: true }
        }

        // History list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: historyVM.histories
            spacing: 6

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 72
                radius: Theme.radiusLg
                color: histItemMouse.containsMouse ? Theme.surfaceVariant : Theme.surface
                border.width: 1
                border.color: Theme.divider

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.spacingMd
                    anchors.rightMargin: Theme.spacingMd
                    spacing: Theme.spacingSm

                    // Date indicator
                    Rectangle {
                        width: 44; height: 44
                        radius: Theme.radiusMd
                        color: Theme.withAlpha(Theme.info, 0.1)

                        Label {
                            anchors.centerIn: parent
                            text: {
                                var d = model.sessionDate || ""
                                return d.length >= 2 ? d.substring(0, 2) : "–"
                            }
                            font.pixelSize: 16
                            font.weight: Font.Bold
                            color: Theme.info
                        }
                    }

                    // Info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.shiftName || "Ca không tên"
                            font: Theme.typography.labelLarge
                            color: Theme.backgroundText
                        }

                        RowLayout {
                            spacing: Theme.spacingSm
                            Label {
                                text: model.sessionDate || ""
                                font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                            }
                            Label {
                                visible: (model.notes || "") !== ""
                                text: model.notes || ""
                                font: Theme.typography.labelSmall; color: Theme.textDisabled
                                elide: Text.ElideRight
                                Layout.maximumWidth: 200
                            }
                        }
                    }

                    // Total
                    Label {
                        text: model.totalAmount ? Number(model.totalAmount).toLocaleString('vi-VN') + " đ" : "0 đ"
                        font: Theme.typography.titleSmall
                        color: Theme.primaryDark
                    }

                    // View detail
                    RoundButton {
                        text: "Chi tiết"
                        width: 64; height: 36
                        flat: true
                        font: Theme.typography.labelSmall
                        onClicked: {
                            historyVM.loadDetail(model.historyId)
                            historyDetailDialog.open()
                        }
                    }

                    // Delete
                    RoundButton {
                        text: "Xóa"
                        width: 48; height: 32
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.error
                        onClicked: deleteHistConfirm.show(
                            "Xóa lịch sử?",
                            "Ca '" + (model.shiftName || "") + "' sẽ bị xóa.",
                            function() { historyVM.deleteHistory(model.historyId) }
                        )
                    }
                }

                MouseArea {
                    id: histItemMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    propagateComposedEvents: true
                    onPressed: function(mouse) { mouse.accepted = false }
                }
            }

            // Empty state
            Label {
                anchors.centerIn: parent
                visible: historyVM.histories.count === 0
                text: "Chưa có lịch sử nào"
                font: Theme.typography.bodyLarge
                color: Theme.textDisabled
            }
        }
    }

    HistoryDetailDialog { id: historyDetailDialog }
    ConfirmDialog { id: deleteHistConfirm }
}
