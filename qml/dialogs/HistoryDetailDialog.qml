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
        spacing: Theme.spacingSm

        // Meta info
        RowLayout {
            Layout.fillWidth: true; spacing: Theme.spacingMd

            Label {
                text: historyVM.selectedDate || ""
                font: Theme.typography.labelLarge
                color: Theme.surfaceVariantText
            }
            Item { Layout.fillWidth: true }
            Label {
                text: historyVM.selectedTotal || "0 đ"
                font: Theme.typography.titleSmall
                color: Theme.primaryDark
            }
        }

        // Notes
        Label {
            visible: (historyVM.selectedNotes || "") !== ""
            text: historyVM.selectedNotes || ""
            font: Theme.typography.labelMedium
            color: Theme.textDisabled
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Header row
        Rectangle {
            Layout.fillWidth: true
            height: 36; radius: Theme.radiusSm; color: Theme.surfaceVariant

            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12
                Label { text: "Sản phẩm"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; Layout.preferredWidth: 160 }
                Label { text: "Giao"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Đóng"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Dùng"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; Layout.preferredWidth: 60; horizontalAlignment: Text.AlignHCenter }
                Label { text: "Thành tiền"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
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
                height: 36; radius: Theme.radiusSm
                color: index % 2 === 0 ? Theme.surface : Theme.backgroundSecondary

                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 12; anchors.rightMargin: 12

                    Label {
                        text: model.productName || ""
                        font: Theme.typography.labelLarge
                        color: Theme.backgroundText
                        Layout.preferredWidth: 160
                        elide: Text.ElideRight
                    }
                    Label {
                        text: model.handoverQty !== undefined ? model.handoverQty : ""
                        font: Theme.typography.labelLarge
                        color: Theme.textSecondary
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.closingQty !== undefined ? model.closingQty : ""
                        font: Theme.typography.labelLarge
                        color: Theme.textSecondary
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.usedQty !== undefined ? model.usedQty : ""
                        font: Theme.typography.labelLarge
                        font.weight: Font.Medium
                        color: Theme.primaryDark
                        Layout.preferredWidth: 60
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: model.amount ? Number(model.amount).toLocaleString('vi-VN') + " đ" : "0 đ"
                        font: Theme.typography.labelLarge
                        font.weight: Font.Medium
                        color: Theme.backgroundText
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
                text: "Xuất Excel"
                flat: true
                Material.foreground: Theme.primary
                onClicked: historyVM.exportHistory(historyVM.selectedHistoryId, "")
            }
        }
    }
}
