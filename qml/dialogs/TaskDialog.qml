import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * TaskDialog — Add or edit a task (type, description, customer, amount, notes).
 */
Dialog {
    id: taskDlg
    title: isEdit ? "Sửa công việc" : "Thêm công việc"
    modal: true
    anchors.centerIn: parent
    width: 440
    standardButtons: Dialog.Save | Dialog.Cancel

    property bool isEdit: false
    property int editTaskId: -1

    function openForNew() {
        isEdit = false
        editTaskId = -1
        typeCombo.currentIndex = 0
        descField.text = ""
        customerField.text = ""
        amountField.text = ""
        notesField.text = ""
        open()
    }

    function openForEdit(taskId, taskType, desc, customer, amount, notes) {
        isEdit = true
        editTaskId = taskId
        // Try to set the combo to the right type
        var types = taskVM.getTaskTypes()
        for (var i = 0; i < types.length; i++) {
            if (types[i] === taskType) { typeCombo.currentIndex = i; break }
        }
        descField.text = desc
        customerField.text = customer
        amountField.text = amount > 0 ? amount.toString() : ""
        notesField.text = notes
        open()
    }

    onOpened: descField.forceActiveFocus()

    onAccepted: {
        var desc = descField.text.trim()
        if (desc === "") return

        if (isEdit) {
            taskVM.updateTask(
                editTaskId,
                typeCombo.currentText,
                desc,
                customerField.text.trim(),
                parseFloat(amountField.text) || 0,
                notesField.text.trim()
            )
        } else {
            taskVM.addTask(
                typeCombo.currentText,
                desc,
                customerField.text.trim(),
                parseFloat(amountField.text) || 0,
                notesField.text.trim()
            )
        }
    }

    ColumnLayout {
        width: parent.width
        spacing: 14

        Label {
            text: isEdit ? "Chỉnh sửa thông tin công việc." : "Thêm công việc / giao dịch mới."
            font: Theme.typography.labelMedium
            color: Theme.surfaceVariantText
            Layout.fillWidth: true
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2; columnSpacing: 12; rowSpacing: 10

            Label { text: "Loại *"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
            ComboBox {
                id: typeCombo
                Layout.fillWidth: true
                model: taskVM.getTaskTypes()
            }

            Label { text: "Mô tả *"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
            TextField {
                id: descField
                Layout.fillWidth: true
                placeholderText: "Mô tả công việc"
            }

            Label { text: "Khách hàng"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
            TextField {
                id: customerField
                Layout.fillWidth: true
                placeholderText: "Tên khách (tùy chọn)"
            }

            Label { text: "Số tiền"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
            TextField {
                id: amountField
                Layout.fillWidth: true
                placeholderText: "0"
                inputMethodHints: Qt.ImhDigitsOnly
            }

            Label { text: "Ghi chú"; color: Theme.textSecondary; font: Theme.typography.labelLarge }
            TextField {
                id: notesField
                Layout.fillWidth: true
                placeholderText: "Ghi chú thêm"
            }
        }
    }
}
