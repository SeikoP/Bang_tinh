import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * SearchField — Material-styled search input.
 */
TextField {
    id: searchField
    placeholderText: "Tìm kiếm..."
    font: Theme.typography.bodyMedium
    leftPadding: 12
    rightPadding: clearBtn.visible ? 36 : 12

    background: Rectangle {
        radius: Theme.radiusMd
        color: searchField.activeFocus ? Theme.surface : Theme.surfaceVariant
        border.width: searchField.activeFocus ? 2 : 1
        border.color: searchField.activeFocus ? Theme.primary : Theme.outline
    }

    // Clear button
    Label {
        id: clearBtn
        text: "×"
        font.pixelSize: 16
        font.weight: Font.Medium
        color: Theme.textDisabled
        visible: searchField.text.length > 0
        anchors.right: parent.right
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter

        MouseArea {
            anchors.fill: parent
            anchors.margins: -4
            cursorShape: Qt.PointingHandCursor
            onClicked: searchField.clear()
        }
    }
}
