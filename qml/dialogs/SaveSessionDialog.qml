import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * SaveSessionDialog — Prompt shift name + notes before saving.
 */
Dialog {
    id: saveSessionDlg
    title: "Lưu Ca"
    modal: true
    anchors.centerIn: parent
    width: 420
    standardButtons: Dialog.Save | Dialog.Cancel

    property string shiftName: ""
    property string notes: ""

    onOpened: {
        shiftField.text = ""
        notesField.text = ""
        shiftField.forceActiveFocus()
    }

    onAccepted: {
        calculationVM.saveSession(shiftField.text, notesField.text)
    }

    ColumnLayout {
        width: parent.width
        spacing: Theme.spacingMd

        Label {
            text: "Nhập tên ca và ghi chú trước khi lưu."
            font: Theme.typography.labelLarge
            color: Theme.surfaceVariantText
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        TextField {
            id: shiftField
            Layout.fillWidth: true
            placeholderText: "Tên ca (VD: Ca sáng 01/01)"
            text: saveSessionDlg.shiftName
        }

        TextField {
            id: notesField
            Layout.fillWidth: true
            placeholderText: "Ghi chú (tùy chọn)"
            text: saveSessionDlg.notes
        }

        // Summary
        Rectangle {
            Layout.fillWidth: true
            height: 48; radius: Theme.radiusSm
            color: Theme.successContainer

            RowLayout {
                anchors.fill: parent; anchors.margins: 12
                Label {
                    text: "Tổng tiền:"
                    font: Theme.typography.labelLarge
                    color: Theme.textSecondary
                }
                Item { Layout.fillWidth: true }
                Label {
                    text: calculationVM.totalAmount
                    font: Theme.typography.titleSmall
                    color: Theme.primaryDark
                }
            }
        }
    }
}
