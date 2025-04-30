package com.example.piganapp

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.activity.ComponentActivity
import com.google.firebase.Firebase
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.auth

class LoginActivity : ComponentActivity() {
    //Create variables to store IDs of layout components
    private lateinit var emailEditTextId: EditText
    private lateinit var passwordEditTextId: EditText
    private lateinit var loginButtonId: Button
    private lateinit var registerButtonId: Button

    //Declare an instance of FirebaseAuth
    private lateinit var auth: FirebaseAuth

    // [START initialize_auth]
    public override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)
        //Initialize Firebase Auth
        auth = Firebase.auth
        // retrieve ID's for layout components
        emailEditTextId = findViewById(R.id.emailEditText)
        passwordEditTextId = findViewById(R.id.passwordEditText)
        loginButtonId = findViewById(R.id.loginButton)
        registerButtonId = findViewById(R.id.goToRegisterButton)

        loginButtonId.setOnClickListener {
            loginUser()
        }

        registerButtonId.setOnClickListener {
            val intent = Intent(this, RegistrationActivity::class.java)
            startActivity(intent)
        }

    }


    // [START on_start_check_user]
    public override fun onStart() {
        super.onStart()
        // Check if user is signed-in (non-null) and update UI accordingly.
        val currentUser = auth.currentUser
        if (currentUser != null) {
            // User is signed in, navigate to MainActivity
            val justSignedInIntent = Intent(this, MainActivity::class.java)
            startActivity(justSignedInIntent)
            finish()  // Make sure to finish LoginActivity so user can't go back
        }
    }
    // [END on_start_check_user]

    /* Current working 4/14/25
    // [START on_start_check_user]
    public override fun onStart() {
        super.onStart()
        //Check if user is signed-in (non-null) and update UI accordingly.
        val currentUser = auth.currentUser
        if (currentUser != null) {
            val signedInIntent = intent
            startActivity(signedInIntent)
        }
    }
    */



    private fun loginUser() {
        val email = emailEditTextId.text.toString().trim()
        val password = passwordEditTextId.text.toString().trim()

        if (email.isEmpty() || password.isEmpty()) {
            Toast.makeText(this, "Please enter email and password", Toast.LENGTH_SHORT).show()
            return
        }

        auth.signInWithEmailAndPassword(email, password)
            .addOnCompleteListener(this) { task ->
                if (task.isSuccessful) {
                    // Sign in success, navigate to the next activity
                    Log.d(TAG, "signInWithEmail:success")
                    val user = auth.currentUser
                    updateUI(user)
                } else {
                    // If sign in fails, display a message to the user.
                    Log.w(TAG, "singInwithEmail:falure", task.exception)
                    Toast.makeText(
                        baseContext,
                        "Authentication failed.",
                        Toast.LENGTH_SHORT
                    ).show()
                    //updateUI(null)
                }
            }
    }

    private fun updateUI(user: FirebaseUser?) {
        //Redirect to next activity
        val justSignedInIntent = Intent(this, MainActivity::class.java)
        startActivity(justSignedInIntent)
        finish()
    }

    companion object {
        private const val TAG = "EmailPassword"
    }
}

