import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * HistoryDetailDialog — Shows line items for a selected session history.
 */
Dialog {
    id: detailDlg
    title: historyVM.selectedShift || "Chi tiết Ca"
    modal: true
    anchors.centerIn: parent
    width: 560
    height: 480
    standardButtons: Dialog.Close

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        // Meta info
        RowLayout {
            Layout.fillWidth: true; spacing: 16

            Label {
                text: "📅 " + (historyVM.selectedDate || "")
                font.pixelSize: 13; color: "#6B7280"
            }
            Item { Layout.fillWidth: true }
            Label {
                text: historyVM.selectedTotal || "0 đ"
                font.pixelSize: 16; font.weight: Font.Bold
                color: "#047857"
            }
        }

        // Notes
        Label {
            visible: (historyVM.selectedNotes || "") !== ""
            text: "📝 " + (historyVM.selectedNotes || "")
            font.pixelSize: 12; color: "#9CA3AF"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Header row
        Rectangle {
            Layout.fillWidth: true
            height: 36; radius: 8; color: "#F3F4F6"

            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                Label { text: "Sản phẩm"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; Layout.preferredWidth: 160 }
                Label { text: "Giao"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Đóng"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Dùng"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Thành tiền"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
            }
        }

        // Items list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: historyVM.detailItems
            spacing: 2

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 36; radius: 6
                color: index % 2 === 0 ? "white" : "#FAFAFA"

                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12

                    Label {
                        text: model.productName || ""
                        font.pixelSize: 13; color: "#1F2937"
                        Layout.preferredWidth: 160
                        elide: Text.ElideRight
                    }
                    Label {
                        text: model.handoverQty !== undefined ? model.handoverQty : ""
                        font.pixelSize: 13; color: "#374151"
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.closingQty !== undefined ? model.closingQty : ""
                        font.pixelSize: 13; color: "#374151"
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.usedQty !== undefined ? model.usedQty : ""
                        font.pixelSize: 13; font.weight: Font.Medium; color: "#047857"
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.amount ? Number(model.amount).toLocaleString('vi-VN') + " đ" : "0 đ"
                        font.pixelSize: 13; font.weight: Font.Medium; color: "#1F2937"
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        // Export row
        RowLayout {
            Layout.fillWidth: true

            Item { Layout.fillWidth: true }

            Button {
                text: "📤 Xuất Excel"
                flat: true
                onClicked: historyVM.exportHistory(historyVM.selectedHistoryId)
            }
        }
    }
}
