package com.example.piganapp
import android.content.Intent
import android.database.Cursor
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.os.CountDownTimer
import android.os.Handler
import android.provider.MediaStore
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.loader.content.CursorLoader
import com.google.firebase.auth.FirebaseAuth
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors


class MainActivity : AppCompatActivity() {
    //define button for camera and imageview type variable
    private lateinit var cameraOpenId: Button
    private lateinit var galleryOpenId: Button
    private lateinit var navigateButtonId: Button //just added 10/29 1:47pm
    lateinit var clickImageId: ImageView
    private val PICK_IMAGE_REQUEST = 1
    private var isImageUploaded = false //Track upload status, just added 10/29 1:47pm

    //new varibles for Camera X 4/14/25 XXXXXXXXXXXXXXX
    private lateinit var previewView: PreviewView
    private lateinit var faceOverlay: View
    private lateinit var imageCapture: ImageCapture
    private lateinit var cameraExecutor: ExecutorService
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // enableEdgeToEdge()
        // edge to edge fills to screen edges, for now will not use, I think it's for newer models
        setContentView(R.layout.activity_main)

        //toolbar 4/15/25 XXXXXXXXXXXXXXXX
        //val toolbar = findViewById<androidx.appcompat.widget.Toolbar>(R.id.toolbar3)
        //setSupportActionBar(toolbar)
        //XXXXXXXXXXXXXXXXXXXXXXXXXXXXX


        // New CameraX preview elements 4/14/25 XXXXXXXXXXXXXXXXXXXXX
        previewView = findViewById(R.id.previewView)
        faceOverlay = findViewById(R.id.faceOverlay)
        // XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        //From ID, get each component (button and imageview); id is assigned in xml file
        cameraOpenId = findViewById(R.id.camera_button)
        galleryOpenId = findViewById(R.id.gallery_button)
        clickImageId = findViewById(R.id.click_image)
        navigateButtonId = findViewById(R.id.navigate_button) //initialize the button, just added 10/29

        // 4/14/24 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        cameraExecutor = Executors.newSingleThreadExecutor()
        // XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


        // 4/14/25 XXXXXXXXXXXXXXXXXXXXXXXXXXXX
        cameraOpenId.setOnClickListener {
            startCamera()
            previewView.visibility = View.VISIBLE
            faceOverlay.visibility = View.VISIBLE
            clickImageId.visibility = View.GONE



            // Start countdown
            val countdownText = findViewById<TextView>(R.id.countdown_text)
            countdownText.visibility = View.VISIBLE

            object : CountDownTimer(5000, 1000) {
                override fun onTick(millisUntilFinished: Long) {
                    countdownText.text = (millisUntilFinished / 1000 + 1).toString() // +1 for more accurate visual countdown
                }

                override fun onFinish() {
                    countdownText.visibility = View.GONE
                    takePhoto()
                }
            }.start()

            /*
            // Auto-take photo after a delay or show another capture button if preferred
            Handler(mainLooper).postDelayed({
                takePhoto()
            }, 3000) // 3 seconds for user to align face */
        }
        // XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        /* Current before cameraX
        //add onClickListener to camera button
        cameraOpenId.setOnClickListener(View.OnClickListener { v: View? ->
            // Create the camera_intent ACTION_IMAGE_CAPTURE it will open the camera for capture the image
            val cameraIntent = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
            // Start the activity with camera_intent, and request pic id
            startActivityForResult(cameraIntent, pic_id)
        }) */




        //add onClickListener to gallery button
        galleryOpenId.setOnClickListener(View.OnClickListener { v: View? ->
            // Create the camera_intent ACTION_IMAGE_CAPTURE it will open the camera for capture the image
            val galleryIntent = Intent(Intent.ACTION_PICK, android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI)
            intent.setType("image/*")
            // Start the activity with gallery intent, and request pic id
            startActivityForResult(galleryIntent, PICK_IMAGE_REQUEST)
        })

        navigateButtonId.setOnClickListener {
            if (isImageUploaded) {
                // Start the next activity
                val intent = Intent(this, EmotionActivity::class.java) // Replace NextActivity with your actual activity class
                startActivity(intent)
                finish()
            } else {
                Toast.makeText(this, "Please upload an image first.", Toast.LENGTH_SHORT).show()
            }
        }

    }


    //menu toolbar logic
    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_logout -> {
                FirebaseAuth.getInstance().signOut()
                val intent = Intent(this, LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
                true
            }

            R.id.action_readTutorial -> {
                val intent = Intent(this, ReadTutorialActivity::class.java)
                startActivity(intent)
                true
            }

            R.id.action_watchTutorial -> {
                val intent = Intent(this, WatchTutorialActivity::class.java)
                startActivity(intent)
                true
            }

            R.id.action_close -> {
                finishAffinity()
                true
            }

            else -> super.onOptionsItemSelected(item)
        }
    }
    //XXXXXXXXXXXXXXXXXXXXXXXXXX





    // 4/14/25 the functions in oncreate XXXXXXXXXXXXXXXXXXXXXXXXXXX

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider: ProcessCameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }

            imageCapture = ImageCapture.Builder()
                .setTargetRotation(previewView.display.rotation)
                .build()

            val cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, imageCapture
                )
            } catch (exc: Exception) {
                Log.e("CameraX", "Use case binding failed", exc)
            }

        }, ContextCompat.getMainExecutor(this))
    }

    private fun takePhoto() {
        val imageFile = File.createTempFile("captured_", ".jpg", cacheDir)

        val outputOptions = ImageCapture.OutputFileOptions.Builder(imageFile).build()

        imageCapture.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(this),
            object : ImageCapture.OnImageSavedCallback {
                override fun onError(exc: ImageCaptureException) {
                    Log.e("CameraX", "Photo capture failed: ${exc.message}", exc)
                }

                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    val savedUri = Uri.fromFile(imageFile)
                    Log.d("CameraX", "Photo capture succeeded: $savedUri")

                    runOnUiThread {
                        previewView.visibility = View.GONE
                        faceOverlay.visibility = View.GONE
                        clickImageId.visibility = View.VISIBLE
                        clickImageId.setImageURI(savedUri)
                    }

                    uploadImage(savedUri)
                }
            }
        )
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX


    //nothing below this was modified for cameraX

    //current version works
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode == RESULT_OK) {
            when (requestCode) {
                pic_id -> {
                    val photo = data?.extras?.get("data") as? Bitmap
                    Log.d("CameraResult", "Photo: $photo")
                    if (photo != null) {
                        // Save the bitmap to a temporary file
                        val imageFile = File.createTempFile("captured_image", ".jpg", cacheDir)
                        FileOutputStream(imageFile).use { outStream ->
                            photo.compress(Bitmap.CompressFormat.JPEG, 100, outStream)
                        }
                        // Use the URI of the temporary file for upload
                        uploadImage(Uri.fromFile(imageFile))

                        // Display the photo in ImageView
                        clickImageId.setImageBitmap(photo)
                    } else {
                        Toast.makeText(this, "No photo captured", Toast.LENGTH_SHORT).show()
                    }
                }
                // Handle gallery request here
                PICK_IMAGE_REQUEST -> {
                    val imageUri: Uri? = data?.data
                    // added 10/22/2024 at 2:35am for image upload to server
                    imageUri?.let { uploadImage(it) }
                    // Now you can use imageUri to display the image or upload it
                    val imageView: ImageView = findViewById(R.id.click_image)
                    imageView.setImageURI(imageUri)
                }
            }
        } else {
            Toast.makeText(this, "Action canceled or failed", Toast.LENGTH_SHORT).show()
        }
    }
    /*
    //old version, was failing to upload image from camera to server
    // This below code works now and can handle retrieving images for both the camera and gallery intent cases
    // Toast is basically a small widget pop up
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode == RESULT_OK) {
            when (requestCode) {
                pic_id -> {

                    // BitMap is data structure of image file which store the image in memory
                    val photo = data!!.extras!!["data"] as Bitmap?
                    //adding for server upload 10/22/2024 3:26am, different for bitmap case
                    val imageFile = File(cacheDir, "captured_image.jpg")
                    val outStream = FileOutputStream(imageFile)
                    photo?.compress(Bitmap.CompressFormat.JPEG, 100, outStream)
                    outStream.flush()
                    outStream.close()
                    uploadImage(Uri.fromFile(imageFile))
                    // Set the image in imageview for display
                    clickImageId.setImageBitmap(photo)

                }
                PICK_IMAGE_REQUEST -> {
                    val imageUri: Uri? = data?.data
                    // added 10/22/2024 at 2:35am for image upload to server
                    imageUri?.let {uploadImage(it)}
                    // Now you can use imageUri to display the image or upload it
                    val imageView: ImageView = findViewById(R.id.click_image)
                    imageView.setImageURI(imageUri)


                }
            }
        } else {
            Toast.makeText(this, "Action canceled or failed", Toast.LENGTH_SHORT).show()
        }
    }
    */

    companion object {
        // Define the pic id
        private const val pic_id = 123
    }


    //new upload start here 1/28/2025
    // tested on 1/28/2025 and works successfully
    private fun uploadImage(imageUri: Uri) {
        // Get the current Firebase user
        val user = FirebaseAuth.getInstance().currentUser
        if (user != null) {
            // Retrieve the Firebase ID token
            user.getIdToken(true).addOnCompleteListener { tokenTask ->
                if (tokenTask.isSuccessful) {
                    val idToken = tokenTask.result?.token

                    // Proceed with the image upload if token is available
                    if (idToken != null) {
                        // Get the input stream from the URI
                        try {
                            val inputStream = contentResolver.openInputStream(imageUri)
                            if (inputStream != null) {
                                // Create a temporary file
                                val tempFile = File.createTempFile("upload", ".jpg", cacheDir)
                                FileOutputStream(tempFile).use { outStream ->
                                    inputStream.copyTo(outStream)
                                }

                                // Create the request body for Retrofit
                                val requestFile = RequestBody.create("image/*".toMediaTypeOrNull(), tempFile)
                                val body = MultipartBody.Part.createFormData("file", tempFile.name, requestFile)

                                // Create Retrofit instance
                                val retrofit = Retrofit.Builder()
                                    .baseUrl("https://close-thankfully-chow.ngrok-free.app") // Replace with server's URL
                                    .addConverterFactory(GsonConverterFactory.create())
                                    .build()

                                // Create an instance of the API interface
                                val ganApi = retrofit.create(GanApi::class.java)

                                // Proceed with the Retrofit API call
                                ganApi.uploadImage(idToken, body).enqueue(object : retrofit2.Callback<ResponseBody> {
                                    override fun onResponse(call: Call<ResponseBody>, response: retrofit2.Response<ResponseBody>) {
                                        if (response.isSuccessful) {
                                            Toast.makeText(this@MainActivity, "Upload successful!", Toast.LENGTH_SHORT).show()
                                            isImageUploaded = true // Update the status after upload
                                        } else {
                                            Toast.makeText(this@MainActivity, "Upload failed: ${response.message()}", Toast.LENGTH_SHORT).show()
                                        }
                                    }

                                    override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                                        Toast.makeText(this@MainActivity, "Failure: ${t.message}", Toast.LENGTH_SHORT).show()
                                    }
                                })
                            } else {
                                Log.e("UploadImage", "Failed to open input stream for URI: $imageUri")
                            }
                        } catch (e: Exception) {
                            Log.e("UploadImage", "Error uploading image: ${e.message}", e)
                        }
                    } else {
                        Log.e("UploadImage", "ID Token is null")
                    }
                } else {
                    Log.e("UploadImage", "Error retrieving ID token: ${tokenTask.exception?.message}")
                }
            }
        } else {
            Log.e("UploadImage", "User is not authenticated")
        }
    }

    //new upload ends here 1/28/2025







    //old upload starts here
    //new verison, handles Uri directly rather than looking for filepath, this is what allows for temporary files to work properly in camera upload

//    private fun uploadImage(imageUri: Uri) {
//        // Get the input stream from the URI
//        try {
//            val inputStream = contentResolver.openInputStream(imageUri)
//            if (inputStream != null) {
//                // Create a temporary file if necessary
//                val tempFile = File.createTempFile("upload", ".jpg", cacheDir)
//                FileOutputStream(tempFile).use { outStream ->
//                    inputStream.copyTo(outStream)
//                }
//
//                // Create request body for Retrofit
//                val requestFile = RequestBody.create("image/*".toMediaTypeOrNull(), tempFile)// 11/19 gave me an error for parse after http3 syncing
//                val body = MultipartBody.Part.createFormData("file", tempFile.name, requestFile)
//
//                // Create Retrofit instance
//                val retrofit = Retrofit.Builder()
//                    .baseUrl("http://192.168.42.13:5000") // Replace with your PC's IP address
//                    .addConverterFactory(GsonConverterFactory.create())
//                    .build()
//
//                // Create an instance of the API interface
//                val ganApi = retrofit.create(GanApi::class.java)
//
//                // Proceed with the Retrofit API call
//                // Example API call (replace with your actual API interface)
//                ganApi.uploadImage(body).enqueue(object : retrofit2.Callback<ResponseBody> {
//                    override fun onResponse(call: Call<ResponseBody>, response: retrofit2.Response<ResponseBody>) {
//                        if (response.isSuccessful) {
//                            Toast.makeText(this@MainActivity, "Upload successful!", Toast.LENGTH_SHORT).show()
//                            isImageUploaded = true //update the status, just added 10/29
//                        } else {
//                            Toast.makeText(this@MainActivity, "Upload failed: ${response.message()}", Toast.LENGTH_SHORT).show()
//                        }
//                    }
//
//                    override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
//                        Toast.makeText(this@MainActivity, "Failure: ${t.message}", Toast.LENGTH_SHORT).show()
//                    }
//                })
//            } else {
//                Log.e("UploadImage", "Failed to open input stream for URI: $imageUri")
//            }
//        } catch (e: Exception) {
//            Log.e("UploadImage", "Error uploading image: ${e.message}", e)
//        }
//    }


    //old upload ends here









    /*
    // Just added for server 10-22-2024, old version, handled filepath rather than Uri directly
    private fun uploadImage(imageUri: Uri) {
        val filePath = getRealPathFromURI(imageUri)
        val file = File(filePath)

        // Create Retrofit instance
        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.213.6.200:5000") // Replace with your PC's IP address
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        // Create an instance of the API interface
        val ganApi = retrofit.create(GanApi::class.java)

        // Create request body
        val requestFile = RequestBody.create(MediaType.parse("image/*"), file)
        val body = MultipartBody.Part.createFormData("file", file.name, requestFile)

        // Make the API call
        ganApi.uploadImage(body).enqueue(object : retrofit2.Callback<ResponseBody> {
            override fun onResponse(call: Call<ResponseBody>, response: retrofit2.Response<ResponseBody>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@MainActivity, "Upload successful!", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@MainActivity, "Upload failed: ${response.message()}", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<ResponseBody>, t: Throwable) {
                Toast.makeText(this@MainActivity, "Failure: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

     */

     */

    //added ? to String and cursor line 125 and 132, new version (this is one isn't as drastic compared to the other changes)
    private fun getRealPathFromURI(contentUri: Uri): String? {
        val proj = arrayOf(MediaStore.Images.Media.DATA)
        val loader = CursorLoader(this, contentUri, proj, null, null, null)
        val cursor: Cursor? = loader.loadInBackground()
        val columnIndex = cursor?.getColumnIndexOrThrow(MediaStore.Images.Media.DATA) ?: -1
        cursor?.moveToFirst()

        return if (cursor != null && columnIndex != -1) {
            cursor.getString(columnIndex)
        } else {
            null // Return null if cursor is invalid or column index is not found
        }
    }

    /*
    //added ? to String and cursor line 125 and 132, old version
    private fun getRealPathFromURI(contentUri: Uri): String {
        val proj = arrayOf(MediaStore.Images.Media.DATA)
        val loader = CursorLoader(this, contentUri, proj, null, null, null)
        val cursor: Cursor? = loader.loadInBackground()
        val column_index = cursor?.getColumnIndexOrThrow(MediaStore.Images.Media.DATA) ?: -1
        cursor?.moveToFirst()
        if (cursor != null) {
            return if (column_index != -1) {
                cursor.getString(column_index)
            } else {
                ""
            }
        }
        return TODO("Provide the return value")
    }
    */
}





