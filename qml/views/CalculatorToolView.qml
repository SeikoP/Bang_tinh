import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * CalculatorToolView — Simple calculator with history panel, keyboard input,
 * special functions (%, 1/x, x², √), and click-to-reuse history.
 */
Item {
    id: calcToolRoot
    focus: true

    // Keyboard input
    Keys.onPressed: function(event) {
        switch (event.key) {
        case Qt.Key_0: case Qt.Key_1: case Qt.Key_2: case Qt.Key_3:
        case Qt.Key_4: case Qt.Key_5: case Qt.Key_6: case Qt.Key_7:
        case Qt.Key_8: case Qt.Key_9:
            calculatorToolVM.inputDigit(event.text); event.accepted = true; break
        case Qt.Key_Plus:
            calculatorToolVM.inputOperator("+"); event.accepted = true; break
        case Qt.Key_Minus:
            calculatorToolVM.inputOperator("-"); event.accepted = true; break
        case Qt.Key_Asterisk:
            calculatorToolVM.inputOperator("*"); event.accepted = true; break
        case Qt.Key_Slash:
            calculatorToolVM.inputOperator("/"); event.accepted = true; break
        case Qt.Key_Period: case Qt.Key_Comma:
            calculatorToolVM.inputDecimal(); event.accepted = true; break
        case Qt.Key_Return: case Qt.Key_Enter: case Qt.Key_Equal:
            calculatorToolVM.calculate(); event.accepted = true; break
        case Qt.Key_Backspace:
            calculatorToolVM.backspace(); event.accepted = true; break
        case Qt.Key_Escape:
            calculatorToolVM.clear(); event.accepted = true; break
        case Qt.Key_Percent:
            calculatorToolVM.percent(); event.accepted = true; break
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingMd

        // Calculator panel
        Pane {
            Layout.preferredWidth: 360
            Layout.fillHeight: true
            Material.elevation: 2
            Material.background: Theme.surface
            padding: 20

            ColumnLayout {
                anchors.fill: parent
                spacing: Theme.spacingSm

                // Expression
                Label {
                    text: calculatorToolVM.expression || " "
                    font: Theme.typography.labelMedium
                    color: Theme.textDisabled
                    horizontalAlignment: Text.AlignRight
                    Layout.fillWidth: true
                }

                // Display
                Rectangle {
                    Layout.fillWidth: true
                    height: 56; radius: Theme.radiusLg
                    color: Theme.backgroundSecondary
                    border.width: 1; border.color: Theme.outline

                    Label {
                        anchors.fill: parent
                        anchors.rightMargin: Theme.spacingMd
                        text: calculatorToolVM.display || "0"
                        font.pixelSize: 28
                        font.weight: Font.Medium
                        color: Theme.backgroundText
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
                    rowSpacing: 6; columnSpacing: 6

                    // Row 0: Special functions — %, 1/x, x², √
                    CalcButton { btnText: "%";   accent: true;  onBtnClicked: calculatorToolVM.percent() }
                    CalcButton { btnText: "1/x"; accent: true;  onBtnClicked: calculatorToolVM.reciprocal() }
                    CalcButton { btnText: "x²";  accent: true;  onBtnClicked: calculatorToolVM.square() }
                    CalcButton { btnText: "√";   accent: true;  onBtnClicked: calculatorToolVM.squareRoot() }

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
            Material.background: Theme.surface
            padding: Theme.spacingMd

            ColumnLayout {
                anchors.fill: parent
                spacing: Theme.spacingSm

                RowLayout {
                    Layout.fillWidth: true

                    Label {
                        text: "Lịch sử tính"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                        Layout.fillWidth: true
                    }

                    Button {
                        text: "Xóa"
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.error
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
                        radius: Theme.radiusSm
                        color: histMouse.containsMouse ? Theme.surfaceVariant : (index % 2 === 0 ? Theme.backgroundSecondary : Theme.surface)

                        Label {
                            anchors.fill: parent
                            anchors.leftMargin: 12; anchors.rightMargin: 12
                            text: modelData || ""
                            font: Theme.typography.labelLarge
                            color: Theme.textSecondary
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }

                        MouseArea {
                            id: histMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                // Extract result from "expr = result" and reuse it
                                var parts = (modelData || "").split("=")
                                if (parts.length > 1)
                                    calculatorToolVM.inputDigit(parts[parts.length - 1].trim())
                            }
                        }
                    }
                }

                Label {
                    visible: calculatorToolVM.history.length === 0
                    text: "Chưa có phép tính nào"
                    font: Theme.typography.labelMedium
                    color: Theme.textDisabled
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
            radius: Theme.radiusMd
            color: {
                if (calcBtn.primary) return calcBtn.pressed ? Theme.primaryDark : Theme.primary
                if (calcBtn.accent) return calcBtn.pressed ? Theme.outline : Theme.surfaceVariant
                return calcBtn.pressed ? Theme.outline : Theme.backgroundSecondary
            }
            border.width: 1
            border.color: calcBtn.primary ? Theme.primaryDark : Theme.outline
        }

        contentItem: Label {
            text: calcBtn.btnText
            font.pixelSize: 18
            font.weight: calcBtn.primary ? Font.Bold : Font.Medium
            color: calcBtn.primary ? Theme.surface : (calcBtn.accent ? Theme.primaryDark : Theme.backgroundText)
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        onClicked: calcBtn.btnClicked()
    }
}
