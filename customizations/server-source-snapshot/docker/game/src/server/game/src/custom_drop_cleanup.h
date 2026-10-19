#pragma once
// CUSTOM_DROP_CLEANUP_RECIPE_BOX_V1
namespace custom_drop_cleanup {
const DWORD RecipeBox=59010;
inline bool Recipe(DWORD v){switch(v){case 50911:case 50912:case 50913:case 50914:case 50915:case 50916:case 50917:case 50918:case 50919:case 50920:case 50921:case 50922:case 50923:case 50924:case 50925:case 50926:case 50927:case 50929:case 50930:case 50932:case 50933:case 50935:case 50942:case 50943:return true;default:return false;}}
inline bool Banned(DWORD v){switch(v){case 27002:case 27003:case 27005:case 27006:case 27117:case 27118:case 27120:case 27121:case 51755:case 51756:case 51760:case 51761:case 51771:case 51772:case 51775:case 51776:case 51791:case 51792:case 51796:case 51797:return true;default:return v>=8101 && v<=8105;}}
}
