// ---- Created with 3Dmigoto v1.3.16 on Thu Mar 19 22:33:02 2026

SamplerState s_cc_tex0_s : register(s0);
Texture2D<float4> CC_Texture0 : register(t0);

// 3Dmigoto declarations
#define cmp -
Texture1D<float4> IniParams : register(t120);
Texture2D<float4> StereoParams : register(t125);

static const float tolerance = 0.1;
bool filterByColor(float3 color, float4 o0) {
  color.xyz = color.xyz / 255.0;
  if (color.x >= o0.x - tolerance && color.x <= o0.x + tolerance &&
      color.y >= o0.y - tolerance && color.y <= o0.y + tolerance &&
      color.z >= o0.z - tolerance && color.z <= o0.z + tolerance) {
    return true;
  }
  return false;
}

void filterText(bool position, bool color, inout float4 o0) {
  if (position && color) { discard; }
}

// v0.xy is already screen pixels — SV_Position in PS is post-viewport coords
bool filterByPosition(float x, float y, float width, float height, float2 pos) {
  return pos.x >= x && pos.x <= (x + width) &&
         pos.y >= y && pos.y <= (y + height);
}

void main(
  float4 v0 : SV_Position0,
  float4 v1 : COLOR0,
  float2 v2 : TEXCOORD0,
  float4 w2 : TEXCOORD1,
  out float4 o0 : SV_Target0)
{
  float4 r0;

  r0.x = CC_Texture0.Sample(s_cc_tex0_s, v2.xy).w;
  o0.xyz = v1.xyz;
  o0.w = v1.w * r0.x;

  float2 pos = v0.xy;

  // Script ID
  if (IniParams[0].w != 0){
    switch ((int)IniParams[0].w) {
      // After Loading Screen Disappears (6 sec)
      case 1:
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(198, 209, 232), o0), o0); // Dikdörtgen 1
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(106, 126, 168), o0), o0); // Dikdörtgen 1
        break;

      // After In Game Detector Texture Disappears (6 sec)
      case 2:
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(198, 209, 232), o0), o0); // Dikdörtgen 1
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(106, 126, 168), o0), o0); // Dikdörtgen 1
        break;
    }
  }

  if (IniParams[0].z != 0){
    switch ((int)IniParams[0].z) {
      // Match Found
      case 7:
        filterText(filterByPosition(303, 477, 375, 37, pos), true, o0); // Dikdörtgen 1
        filterText(filterByPosition(305, 733, 362, 39, pos), true, o0); // Dikdörtgen 2
        filterText(filterByPosition(1286, 608, 259, 48, pos), true, o0); // Dikdörtgen 3
        break;
    }
  }

  if (IniParams[0].y != 0) {
    switch ((int)IniParams[0].y) {
      // Chat
      case 1:
        filterText(filterByPosition(193, 88, 264, 898, pos), filterByColor(float3(203, 220, 246), o0), o0);
        break;

      case 2:                
        // Custom || Match Room - Chat
        if (IniParams[0].x == 3 || IniParams[0].x == 4) { 
          filterText(filterByPosition(1260, -1, 193, 134, pos), true, o0); // Top Right Small Chat
          } else { // Any Chat
            filterText(filterByPosition(653, 934, 216, 146, pos), true, o0); // Bottom Center Small Chat
          }
        break;

      case 3:
        filterText(filterByPosition(448, 843, 125, 42, pos), true, o0); // Dikdörtgen 1
        filterText(filterByPosition(418, 886, 133, 39, pos), true, o0); // Dikdörtgen 2
        break;

      case 4:
        filterText(filterByPosition(420, 482, 108, 38, pos), filterByColor(float3(245, 246, 247), o0), o0); // Dikdörtgen 1
        break;
    }
  }

  if (IniParams[0].x != 0) {
    switch ((int)IniParams[0].x) {
      // Profile
      case 1:
        filterText(filterByPosition(1220, 161, 104, 36, pos), true, o0); // ID
        filterText(filterByPosition(1130,  93, 240, 48, pos), true, o0); // Name

        break;

      // Add Friends
      case 2:
        filterText(filterByPosition(1259, 557, 182, 44, pos), true, o0); // ID 4
        filterText(filterByPosition(563, 377, 182, 44, pos), true, o0); // ID 1
        filterText(filterByPosition(563, 557, 182, 44, pos), true, o0); // ID 2
        filterText(filterByPosition(563, 738, 182, 44, pos), true, o0); // ID 3
        filterText(filterByPosition(1259, 738, 182, 44, pos), true, o0); // ID 5
        filterText(filterByPosition(1259, 377, 182, 44, pos), true, o0); // ID 6
        break;

      // Custom Match Room
      case 3:
        filterText(filterByPosition(344, 161, 797, 37, pos), filterByColor(float3(203, 220, 246), o0), o0); // Spectators
        switch ((int)IniParams[0].z) {
          // Frenzy Rhapsody
          case 1:          
            filterText(filterByPosition(280, 470, 579, 48, pos), true, o0); // Dikdörtgen 1 kopya
            filterText(filterByPosition(280, 631, 579, 48, pos), true, o0); // Dikdörtgen 1 kopya 5
            filterText(filterByPosition(280, 781, 579, 48, pos), true, o0); // Dikdörtgen 1 kopya 6
            break;

          // Chasing Shadows
          case 2:
            filterText(filterByPosition(247, 493, 684, 48, pos), true, o0); // Dikdörtgen 1 kopya
            filterText(filterByPosition(247, 654, 684, 48, pos), true, o0); // Dikdörtgen 1 kopya 5
            filterText(filterByPosition(247, 804, 684, 48, pos), true, o0); // Dikdörtgen 1 kopya 6    
            break;

          // Enchanted Forest
          case 3:
            filterText(filterByPosition(186, 321, 1627, 48, pos), true, o0); // Dikdörtgen 1 kopya
            filterText(filterByPosition(186, 482, 1627, 48, pos), true, o0); // Dikdörtgen 1 kopya 5
            filterText(filterByPosition(186, 632, 1627, 48, pos), true, o0); // Dikdörtgen 1 kopya 6
            filterText(filterByPosition(186, 793, 853, 48, pos), true, o0); // Dikdörtgen 1 kopya 7          
            break;
          
          // Blackjack
          case 4:
            filterText(filterByPosition(425, 256, 319, 48, pos), true, o0); // Dikdörtgen 1 kopya
            filterText(filterByPosition(559, 399, 319, 48, pos), true, o0); // Dikdörtgen 1 kopya 2
            filterText(filterByPosition(626, 542, 319, 48, pos), true, o0); // Dikdörtgen 1 kopya 3
            filterText(filterByPosition(559, 701, 319, 48, pos), true, o0); // Dikdörtgen 1 kopya 4
            filterText(filterByPosition(413, 844, 319, 48, pos), true, o0); // Dikdörtgen 1 kopya 5
            break;
          
          // Duo Training
          case 5:
            filterText(filterByPosition(211, 406, 579, 43, pos), true, o0); // Dikdörtgen 3
            break;

          default:
            filterText(filterByPosition(188, 365, 853, 48, pos), true, o0); // Dikdörtgen 1 kopya
            filterText(filterByPosition(188, 526, 853, 48, pos), true, o0); // Dikdörtgen 1 kopya 5
            filterText(filterByPosition(188, 676, 853, 48, pos), true, o0); // Dikdörtgen 1 kopya 6
            filterText(filterByPosition(188, 831, 853, 48, pos), true, o0); // Dikdörtgen 1 kopya 7
            break;
        }

        break;
      // Match Room  
      case 4:
        filterText(filterByPosition(1, 246, 1919, 321, pos), filterByColor(float3(146, 128, 89), o0), o0); // Dikdörtgen 1
        filterText(filterByPosition(1, 246, 1919, 321, pos), filterByColor(float3(162, 162, 160), o0), o0); // Dikdörtgen 1
        break;

      // In Game
      case 5:
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(198, 209, 232), o0), o0); // Names
        filterText(filterByPosition(1252, 169, 659, 45, pos), filterByColor(float3(106, 126, 168), o0), o0); // Name Shadows
        filterText(filterByPosition(91, 269, 726, 59, pos), filterByColor(float3(255, 255, 255), o0), o0); // Announcements
        filterText(filterByPosition(91, 269, 726, 59, pos), filterByColor(float3(105, 113, 139), o0), o0); // Announcement Shadows

        break;
      
      // End Game
      case 7:
        filterText(filterByPosition(261, 803, 168, 37, pos), true, o0); // Dikdörtgen 1
        filterText(filterByPosition(633, 803, 168, 37, pos), true, o0); // Dikdörtgen 1 kopya
        filterText(filterByPosition(1013, 803, 168, 37, pos), true, o0); // Dikdörtgen 1 kopya 2
        filterText(filterByPosition(1413, 803, 168, 37, pos), true, o0); // Dikdörtgen 1 kopya 3
        filterText(filterByPosition(1226, 128, 168, 37, pos), true, o0); // Dikdörtgen 1 kopya 4
        break;
    }      
  }
}

/*~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
//
// Generated by Microsoft (R) HLSL Shader Compiler 10.1
//
//   using 3Dmigoto v1.3.16 on Thu Mar 19 22:33:02 2026
//
//
// Resource Bindings:
//
// Name                                 Type  Format         Dim Slot Elements
// ------------------------------ ---------- ------- ----------- ---- --------
// s_cc_tex0                         sampler      NA          NA    0        1
// CC_Texture0                       texture  float4          2d    0        1
//
//
//
// Input signature:
//
// Name                 Index   Mask Register SysValue  Format   Used
// -------------------- ----- ------ -------- -------- ------- ------
// SV_Position              0   xyzw        0      POS   float
// COLOR                    0   xyzw        1     NONE   float   xyzw
// TEXCOORD                 0   xy          2     NONE   float   xy
// TEXCOORD                 1     zw        2     NONE   float
//
//
// Output signature:
//
// Name                 Index   Mask Register SysValue  Format   Used
// -------------------- ----- ------ -------- -------- ------- ------
// SV_Target                0   xyzw        0   TARGET   float   xyzw
//
ps_5_0
dcl_globalFlags refactoringAllowed
dcl_sampler s0, mode_default
dcl_resource_texture2d (float,float,float,float) t0
dcl_input_ps linear v1.xyzw
dcl_input_ps linear v2.xy
dcl_output o0.xyzw
dcl_temps 1
sample_indexable(texture2d)(float,float,float,float) r0.x, v2.xyxx, t0.wxyz, s0
mul o0.w, r0.x, v1.w
mov o0.xyz, v1.xyzx
ret
// Approximately 4 instruction slots used

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/
