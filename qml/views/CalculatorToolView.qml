import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * CalculatorToolView — Simple calculator with history panel.
 */
Item {
    id: calcToolRoot

    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16

        // Calculator panel
        Pane {
            Layout.preferredWidth: 340
            Layout.fillHeight: true
            Material.elevation: 2
            Material.background: "white"
            padding: 20

            ColumnLayout {
                anchors.fill: parent
                spacing: 12

                // Expression
                Label {
                    text: calculatorToolVM.expression || " "
                    font.pixelSize: 13; color: "#9CA3AF"
                    horizontalAlignment: Text.AlignRight
                    Layout.fillWidth: true
                }

                // Display
                Rectangle {
                    Layout.fillWidth: true
                    height: 56; radius: 12
                    color: "#F9FAFB"
                    border.width: 1; border.color: "#E5E7EB"

                    Label {
                        anchors.fill: parent
                        anchors.rightMargin: 16
                        text: calculatorToolVM.display || "0"
                        font.pixelSize: 28
                        font.weight: Font.Medium
                        color: "#1F2937"
                        horizontalAlignment: Text.AlignRight
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideLeft
                    }
                }

                // Button grid
                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    columns: 4
                    rowSpacing: 8; columnSpacing: 8

                    // Row 1: C, CE, ⌫, ÷
                    CalcButton { btnText: "C";  accent: false; onBtnClicked: calculatorToolVM.clear() }
                    CalcButton { btnText: "CE"; accent: false; onBtnClicked: calculatorToolVM.clearEntry() }
                    CalcButton { btnText: "⌫";  accent: false; onBtnClicked: calculatorToolVM.backspace() }
                    CalcButton { btnText: "÷";  accent: true;  onBtnClicked: calculatorToolVM.inputOperator("/") }

                    // Row 2: 7, 8, 9, ×
                    CalcButton { btnText: "7"; onBtnClicked: calculatorToolVM.inputDigit("7") }
                    CalcButton { btnText: "8"; onBtnClicked: calculatorToolVM.inputDigit("8") }
                    CalcButton { btnText: "9"; onBtnClicked: calculatorToolVM.inputDigit("9") }
                    CalcButton { btnText: "×"; accent: true; onBtnClicked: calculatorToolVM.inputOperator("*") }

                    // Row 3: 4, 5, 6, −
                    CalcButton { btnText: "4"; onBtnClicked: calculatorToolVM.inputDigit("4") }
                    CalcButton { btnText: "5"; onBtnClicked: calculatorToolVM.inputDigit("5") }
                    CalcButton { btnText: "6"; onBtnClicked: calculatorToolVM.inputDigit("6") }
                    CalcButton { btnText: "−"; accent: true; onBtnClicked: calculatorToolVM.inputOperator("-") }

                    // Row 4: 1, 2, 3, +
                    CalcButton { btnText: "1"; onBtnClicked: calculatorToolVM.inputDigit("1") }
                    CalcButton { btnText: "2"; onBtnClicked: calculatorToolVM.inputDigit("2") }
                    CalcButton { btnText: "3"; onBtnClicked: calculatorToolVM.inputDigit("3") }
                    CalcButton { btnText: "+"; accent: true; onBtnClicked: calculatorToolVM.inputOperator("+") }

                    // Row 5: ±, 0, ., =
                    CalcButton { btnText: "±"; onBtnClicked: calculatorToolVM.negate() }
                    CalcButton { btnText: "0"; onBtnClicked: calculatorToolVM.inputDigit("0") }
                    CalcButton { btnText: "."; onBtnClicked: calculatorToolVM.inputDecimal() }
                    CalcButton { btnText: "="; primary: true; onBtnClicked: calculatorToolVM.calculate() }
                }
            }
        }

        // History panel
        Pane {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Material.elevation: 1
            Material.background: "white"
            padding: 16

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        text: "📋 Lịch sử tính"
                        font.pixelSize: 15; font.weight: Font.Medium
                        color: "#1F2937"
                        Layout.fillWidth: true
                    }

                    RoundButton {
                        text: "🗑️"; flat: true
                        width: 32; height: 32
                        onClicked: calculatorToolVM.clearHistory()
                    }
                }

                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: calculatorToolVM.history
                    spacing: 4

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        width: parent ? parent.width : 0
                        height: 40
                        radius: 8
                        color: index % 2 === 0 ? "#F9FAFB" : "white"

                        Label {
                            anchors.fill: parent
                            anchors.leftMargin: 12; anchors.rightMargin: 12
                            text: modelData || ""
                            font.pixelSize: 13
                            color: "#374151"
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                Label {
                    visible: calculatorToolVM.history.length === 0
                    text: "Chưa có phép tính nào"
                    font.pixelSize: 13; color: "#9CA3AF"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }

    // Inline calc button component
    component CalcButton: AbstractButton {
        id: calcBtn
        property string btnText: ""
        property bool accent: false
        property bool primary: false
        signal btnClicked()

        Layout.fillWidth: true
        Layout.fillHeight: true

        background: Rectangle {
            radius: 10
            color: {
                if (calcBtn.primary) return calcBtn.pressed ? "#059669" : "#10b981"
                if (calcBtn.accent) return calcBtn.pressed ? "#E5E7EB" : "#F3F4F6"
                return calcBtn.pressed ? "#E5E7EB" : "#F9FAFB"
            }
            border.width: 1
            border.color: calcBtn.primary ? "#059669" : "#E5E7EB"
        }

        contentItem: Label {
            text: calcBtn.btnText
            font.pixelSize: 20
            font.weight: calcBtn.primary ? Font.Bold : Font.Medium
            color: calcBtn.primary ? "white" : (calcBtn.accent ? "#047857" : "#1F2937")
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        onClicked: calcBtn.btnClicked()
    }
}
