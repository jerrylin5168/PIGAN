package com.example.piganapp

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface GanApi{
    @Multipart
    @POST("/upload")
    //fun uploadImage(@Part file: MultipartBody.Part): Call<ResponseBody>
    // below was added 1/28/2025 for authentication
    fun uploadImage(
        @Header("Authorization") authHeader: String, // Accept the Authorization header
        @Part file: MultipartBody.Part
    ): Call<ResponseBody>

    @POST("/receive_input")
    //fun sendDropdownSelections(@Body requestBody: DropdownInputData): Call<ResponseBody>
    // below was added 1/28/2025 for authentication
    fun sendDropdownSelectionsWithAuth(
        @Header("Authorization") token: String,
        @Body data: DropdownInputData
    ): Call<ResponseBody>


    @POST("/generate")
    //fun generateImage(@Body requestBody: RequestBody): Call<ResponseBody>
    fun generateImageWithAuth(
        @Header("Authorization") token: String,
        @Body requestBody: RequestBody
    ): Call<ResponseBody>

}

data class DropdownInputData(
    val dropdown1: String,
    val dropdown2: String
)