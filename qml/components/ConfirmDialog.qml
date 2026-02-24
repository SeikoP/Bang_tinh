import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * ConfirmDialog — Reusable Material confirm dialog.
 *
 * Usage:
 *   confirmDialog.show("Delete?", "This cannot be undone.", function() { doDelete() })
 */
Dialog {
    id: confirmDlg
    modal: true
    anchors.centerIn: parent
    width: 380
    standardButtons: Dialog.Ok | Dialog.Cancel
    Material.accent: Theme.primary

    property string message: ""
    property var onConfirm: null

    function show(title, msg, callback) {
        confirmDlg.title = title
        confirmDlg.message = msg
        confirmDlg.onConfirm = callback
        confirmDlg.open()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Theme.spacingMd

        Label {
            text: confirmDlg.message
            font: Theme.typography.bodyMedium
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }

    onAccepted: {
        if (onConfirm) onConfirm()
    }
}
