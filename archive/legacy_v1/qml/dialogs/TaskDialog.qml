import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * TaskDialog — Add a new task (type, description, customer, amount, notes).
 */
Dialog {
    id: taskDlg
    title: "Thêm công việc"
    modal: true
    anchors.centerIn: parent
    width: 440
    standardButtons: Dialog.Save | Dialog.Cancel

    onOpened: {
        typeCombo.currentIndex = 0
        descField.text = ""
        customerField.text = ""
        amountField.text = ""
        notesField.text = ""
        descField.forceActiveFocus()
    }

    onAccepted: {
        var desc = descField.text.trim()
        if (desc === "") return

        taskVM.addTask(
            typeCombo.currentText,
            desc,
            customerField.text.trim(),
            parseFloat(amountField.text) || 0,
            notesField.text.trim()
        )
    }

    ColumnLayout {
        width: parent.width
        spacing: 14

        Label {
            text: "Thêm công việc / giao dịch mới."
            font.pixelSize: 12; color: "#6B7280"
            Layout.fillWidth: true
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2; columnSpacing: 12; rowSpacing: 10

            Label { text: "Loại *"; color: "#374151" }
            ComboBox {
                id: typeCombo
                Layout.fillWidth: true
                model: taskVM.getTaskTypes()
            }

            Label { text: "Mô tả *"; color: "#374151" }
            TextField {
                id: descField
                Layout.fillWidth: true
                placeholderText: "Mô tả công việc"
            }

            Label { text: "Khách hàng"; color: "#374151" }
            TextField {
                id: customerField
                Layout.fillWidth: true
                placeholderText: "Tên khách (tùy chọn)"
            }

            Label { text: "Số tiền"; color: "#374151" }
            TextField {
                id: amountField
                Layout.fillWidth: true
                placeholderText: "0"
                inputMethodHints: Qt.ImhDigitsOnly
            }

            Label { text: "Ghi chú"; color: "#374151" }
            TextField {
                id: notesField
                Layout.fillWidth: true
                placeholderText: "Ghi chú thêm"
            }
        }
    }
}
