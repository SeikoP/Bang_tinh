import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * QuickBankPeek — Hold-to-reveal popup showing recent bank transactions.
 */
Popup {
    id: peekPopup
    width: 350
    height: Math.min(peekContent.implicitHeight + 32, 400)
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    padding: 0

    background: Rectangle {
        radius: 12
        color: "white"
        border.width: 1
        border.color: "#E5E7EB"

        // Shadow simulation
        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            radius: 14
            color: Qt.rgba(0, 0, 0, 0.08)
            z: -1
        }
    }

    ColumnLayout {
        id: peekContent
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            text: "💰 Giao dịch gần đây"
            font.pixelSize: 14
            font.weight: Font.Medium
            color: "#1F2937"
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#E5E7EB"
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 100
            clip: true
            model: bankVM.notifications
            spacing: 4

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 48
                radius: 8
                color: index % 2 === 0 ? "white" : "#F9FAFB"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 8

                    Label {
                        text: "💳"
                        font.pixelSize: 16
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.senderName || ""
                            font.pixelSize: 12
                            font.weight: Font.Medium
                            color: "#1F2937"
                            elide: Text.ElideRight
                        }

                        Label {
                            text: (model.source || "") + " • " + (model.timeStr || "")
                            font.pixelSize: 10
                            color: "#6B7280"
                        }
                    }

                    Label {
                        text: model.amount || ""
                        font.pixelSize: 13
                        font.weight: Font.Bold
                        color: "#10B981"
                    }
                }
            }
        }
    }
}
