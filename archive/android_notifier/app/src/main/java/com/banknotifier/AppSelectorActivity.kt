package com.banknotifier

import android.content.Context
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.graphics.drawable.Drawable
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.CheckBox
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class AppSelectorActivity : AppCompatActivity() {

    data class AppInfo(
        val name: String,
        val packageName: String,
        val icon: Drawable,
        var isSelected: Boolean = false
    )

    private lateinit var recyclerView: RecyclerView
    private lateinit var saveButton: Button
    private lateinit var searchInput: android.widget.EditText
    
    private val allAppsList = mutableListOf<AppInfo>()
    private val filteredList = mutableListOf<AppInfo>()
    private val selectedPackages = mutableSetOf<String>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_app_selector)

        val prefs = getSharedPreferences("BankNotifier", Context.MODE_PRIVATE)
        selectedPackages.addAll(prefs.getStringSet("guarded_apps", emptySet()) ?: emptySet())

        recyclerView = findViewById(R.id.appRecyclerView)
        saveButton = findViewById(R.id.saveAppsButton)
        searchInput = findViewById(R.id.appSearchInput)
        val manualInput = findViewById<android.widget.EditText>(R.id.manualPackageInput)
        val addManualBtn = findViewById<Button>(R.id.addManualBtn)

        recyclerView.layoutManager = LinearLayoutManager(this)
        
        loadApps()

        addManualBtn.setOnClickListener {
            val pkg = manualInput.text.toString().trim()
            if (pkg.isNotEmpty()) {
                val exists = allAppsList.any { it.packageName == pkg }
                if (!exists) {
                    // Try to get app info for the manual package
                    try {
                        val pm = packageManager
                        val app = pm.getApplicationInfo(pkg, 0)
                        val name = app.loadLabel(pm).toString()
                        val icon = app.loadIcon(pm)
                        val newApp = AppInfo(name, pkg, icon, true)
                        allAppsList.add(0, newApp)
                        filterApps("") // Refresh
                        manualInput.setText("")
                        Toast.makeText(this, "✅ Đã thêm: $name", Toast.LENGTH_SHORT).show()
                    } catch (e: Exception) {
                        // If app not installed, we can still add it but with generic icon
                        val newApp = AppInfo("Thủ công: $pkg", pkg, getDrawable(android.R.drawable.sym_def_app_icon)!!, true)
                        allAppsList.add(0, newApp)
                        filterApps("")
                        manualInput.setText("")
                        Toast.makeText(this, "⚠️ Đã thêm thủ công (Package chưa cài đặt hoặc ko tìm thấy)", Toast.LENGTH_SHORT).show()
                    }
                } else {
                    Toast.makeText(this, "ℹ️ App đã có trong danh sách", Toast.LENGTH_SHORT).show()
                }
            }
        }

        saveButton.setOnClickListener {
            val toSave = allAppsList.filter { it.isSelected }.map { it.packageName }.toSet()
            prefs.edit().putStringSet("guarded_apps", toSave).apply()
            Toast.makeText(this, "✅ Đã lưu danh sách bảo vệ: ${toSave.size} ứng dụng", Toast.LENGTH_SHORT).show()
            finish()
        }

        searchInput.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                filterApps(s.toString())
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
    }

    private fun loadApps() {
        AppExecutors.diskIO.execute {
            val pm = packageManager
            val packages = pm.getInstalledApplications(PackageManager.GET_META_DATA)
            
            val tempApps = mutableListOf<AppInfo>()
            for (app in packages) {
                // Keep only apps that have a launch intent (otherwise we can't 'poke' them)
                val launchIntent = pm.getLaunchIntentForPackage(app.packageName)
                // if (launchIntent == null) continue  <-- Removed check to show ALL apps
                
                // Allow system apps if they have a launch intent (many bank apps are bundled/system)
                if (app.packageName == packageName) continue

                val name = app.loadLabel(pm).toString()
                val icon = app.loadIcon(pm)
                val isSelected = selectedPackages.contains(app.packageName)
                
                tempApps.add(AppInfo(name, app.packageName, icon, isSelected))
            }
            
            // Prioritize: 1. Selected, 2. Bank/Pay keywords, 3. Alphabetical
            val bankKeywords = listOf("bank", "pay", "momo", "vnpay", "acb", "bidv", "tcb", "vcb", "mb")
            tempApps.sortWith(compareByDescending<AppInfo> { it.isSelected }
                .thenByDescending { app -> 
                    val lowerName = app.name.lowercase()
                    val lowerPkg = app.packageName.lowercase()
                    bankKeywords.any { lowerName.contains(it) || lowerPkg.contains(it) }
                }
                .thenBy { it.name.lowercase() }
            )

            runOnUiThread {
                allAppsList.clear()
                allAppsList.addAll(tempApps)
                filteredList.clear()
                filteredList.addAll(allAppsList)
                recyclerView.adapter = AppAdapter(filteredList)
            }
        }
    }

    private fun filterApps(query: String) {
        val q = query.lowercase()
        filteredList.clear()
        if (q.isEmpty()) {
            filteredList.addAll(allAppsList)
        } else {
            allAppsList.forEach {
                if (it.name.lowercase().contains(q) || it.packageName.lowercase().contains(q)) {
                    filteredList.add(it)
                }
            }
        }
        recyclerView.adapter?.notifyDataSetChanged()
    }

    class AppAdapter(private val items: List<AppInfo>) : RecyclerView.Adapter<AppAdapter.ViewHolder>() {
        
        class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
            val icon: ImageView = view.findViewById(R.id.appIcon)
            val name: TextView = view.findViewById(R.id.appName)
            val pkg: TextView = view.findViewById(R.id.packageName)
            val checkBox: CheckBox = view.findViewById(R.id.appCheckBox)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.item_app, parent, false)
            return ViewHolder(view)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val item = items[position]
            holder.icon.setImageDrawable(item.icon)
            holder.name.text = item.name
            holder.pkg.text = item.packageName
            
            // Critical for filtering: remove listener before setting checked state
            holder.checkBox.setOnCheckedChangeListener(null)
            holder.checkBox.isChecked = item.isSelected

            val toggleAction = {
                item.isSelected = !item.isSelected
                holder.checkBox.isChecked = item.isSelected
            }

            holder.itemView.setOnClickListener { toggleAction() }
            holder.checkBox.setOnClickListener { toggleAction() }
        }

        override fun getItemCount() = items.size
    }
}
