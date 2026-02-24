import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * HistoryView — Session history list with detail dialog.
 */
Item {
    id: historyViewRoot

    Component.onCompleted: historyVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "📜 Lịch sử Ca"
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#1F2937"
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
                radius: 12
                color: histItemMouse.containsMouse ? "#F3F4F6" : "white"
                border.width: 1
                border.color: "#F3F4F6"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 12

                    // Date icon
                    Rectangle {
                        width: 44; height: 44
                        radius: 10
                        color: "#dbeafe"

                        Label {
                            anchors.centerIn: parent
                            text: "📅"
                            font.pixelSize: 20
                        }
                    }

                    // Info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.shiftName || "Ca không tên"
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            color: "#1F2937"
                        }

                        RowLayout {
                            spacing: 12
                            Label {
                                text: model.sessionDate || ""
                                font.pixelSize: 12; color: "#6B7280"
                            }
                            Label {
                                visible: (model.notes || "") !== ""
                                text: "📝 " + (model.notes || "")
                                font.pixelSize: 11; color: "#9CA3AF"
                                elide: Text.ElideRight
                                Layout.maximumWidth: 200
                            }
                        }
                    }

                    // Total
                    Label {
                        text: model.totalAmount ? Number(model.totalAmount).toLocaleString('vi-VN') + " đ" : "0 đ"
                        font.pixelSize: 16
                        font.weight: Font.Bold
                        color: "#047857"
                    }

                    // View detail
                    RoundButton {
                        text: "👁️"
                        width: 36; height: 36
                        flat: true
                        onClicked: {
                            historyVM.loadDetail(model.historyId)
                            historyDetailDialog.open()
                        }
                    }

                    // Delete
                    RoundButton {
                        text: "🗑️"
                        width: 32; height: 32
                        flat: true
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
                font.pixelSize: 16
                color: "#9CA3AF"
            }
        }
    }

    HistoryDetailDialog { id: historyDetailDialog }
    ConfirmDialog { id: deleteHistConfirm }
}
