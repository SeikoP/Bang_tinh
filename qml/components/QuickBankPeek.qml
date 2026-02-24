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
        radius: Theme.radiusLg
        color: Theme.surface
        border.width: 1
        border.color: Theme.outline

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
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingSm

        Label {
            text: "Giao dịch gần đây"
            font: Theme.typography.titleSmall
            color: Theme.backgroundText
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Theme.outline
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
                radius: Theme.radiusMd
                color: index % 2 === 0 ? Theme.surface : Theme.backgroundSecondary

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.spacingSm
                    anchors.rightMargin: Theme.spacingSm
                    spacing: Theme.spacingSm

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.senderName || ""
                            font: Theme.typography.labelMedium
                            color: Theme.backgroundText
                            elide: Text.ElideRight
                        }

                        Label {
                            text: (model.source || "") + " · " + (model.timeStr || "")
                            font: Theme.typography.labelSmall
                            color: Theme.surfaceVariantText
                        }
                    }

                    Label {
                        text: model.amount || ""
                        font.pixelSize: 13
                        font.weight: Font.Bold
                        color: Theme.primary
                    }
                }
            }
        }
    }
}
