import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * ProductDialog — Add or edit a product (name, unit, conversion, price).
 */
Dialog {
    id: productDlg
    title: isEdit ? "Sửa sản phẩm" : "Thêm sản phẩm"
    modal: true
    anchors.centerIn: parent
    width: 440
    standardButtons: Dialog.Save | Dialog.Cancel

    property bool isEdit: false
    property int editIndex: -1
    property string productName: ""
    property string unit: ""
    property real conversionRate: 1.0
    property real price: 0

    function openForNew() {
        isEdit = false
        editIndex = -1
        productName = ""
        unit = ""
        conversionRate = 1.0
        price = 0
        open()
    }

    function openForEdit(idx, name, u, conv, p) {
        isEdit = true
        editIndex = idx
        productName = name
        unit = u
        conversionRate = conv
        price = p
        open()
    }

    onOpened: nameField.forceActiveFocus()

    onAccepted: {
        var n = nameField.text.trim()
        var u = unitField.text.trim()
        var c = parseFloat(convField.text) || 1.0
        var p = parseFloat(priceField.text) || 0

        if (n === "") return

        if (isEdit) {
            productVM.updateProduct(editIndex, n, u, c, p)
        } else {
            productVM.addProduct(n, u, c, p)
        }
    }

    ColumnLayout {
        width: parent.width
        spacing: 14

        Label {
            text: "Điền thông tin sản phẩm bên dưới."
            font.pixelSize: 12; color: "#6B7280"
            Layout.fillWidth: true
        }

        GridLayout {
            Layout.fillWidth: true
            columns: 2; columnSpacing: 12; rowSpacing: 10

            Label { text: "Tên sản phẩm *"; color: "#374151" }
            TextField {
                id: nameField
                Layout.fillWidth: true
                text: productDlg.productName
                placeholderText: "VD: Bia 333"
            }

            Label { text: "Đơn vị"; color: "#374151" }
            TextField {
                id: unitField
                Layout.fillWidth: true
                text: productDlg.unit
                placeholderText: "VD: thùng, lon, chai"
            }

            Label { text: "Quy đổi"; color: "#374151" }
            TextField {
                id: convField
                Layout.fillWidth: true
                text: productDlg.conversionRate.toString()
                placeholderText: "1.0"
                inputMethodHints: Qt.ImhFormattedNumbersOnly
            }

            Label { text: "Giá (đ)"; color: "#374151" }
            TextField {
                id: priceField
                Layout.fillWidth: true
                text: productDlg.price.toString()
                placeholderText: "0"
                inputMethodHints: Qt.ImhDigitsOnly
            }
        }
    }
}
