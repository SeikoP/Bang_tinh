import QtQuick
import QtQuick.Controls.Material

/**
 * LoadingSpinner — Animated busy indicator overlay.
 * Set 'active' to true to show.
 */
Item {
    id: spinnerRoot
    anchors.fill: parent
    visible: active
    z: 100

    property bool active: false
    property string message: ""

    // Semi-transparent overlay
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.3)
        opacity: spinnerRoot.active ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }

        MouseArea { anchors.fill: parent }  // Block clicks through
    }

    Column {
        anchors.centerIn: parent
        spacing: 16

        BusyIndicator {
            anchors.horizontalCenter: parent.horizontalCenter
            running: spinnerRoot.active
            Material.accent: "#10b981"
            width: 48
            height: 48
        }

        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: spinnerRoot.message
            font.pixelSize: 14
            color: "white"
            visible: spinnerRoot.message !== ""
        }
    }
}
