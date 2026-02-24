import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * SearchField — Material-styled search input with icon.
 */
TextField {
    id: searchField
    placeholderText: "Tìm kiếm..."
    font.pixelSize: 14
    leftPadding: 36
    rightPadding: clearBtn.visible ? 36 : 12

    background: Rectangle {
        radius: 8
        color: searchField.activeFocus ? "white" : "#F3F4F6"
        border.width: searchField.activeFocus ? 2 : 1
        border.color: searchField.activeFocus ? "#10b981" : "#E5E7EB"

        Label {
            text: "🔍"
            font.pixelSize: 14
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.verticalCenter: parent.verticalCenter
            opacity: 0.5
        }
    }

    // Clear button
    Label {
        id: clearBtn
        text: "✕"
        font.pixelSize: 12
        color: "#9CA3AF"
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
