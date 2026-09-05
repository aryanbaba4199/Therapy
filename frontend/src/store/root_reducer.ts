import { combineReducers } from "@reduxjs/toolkit";
import { baseApi } from "./api/base_api";
import { authReducer } from "../features/auth/store/auth_slice";

export const rootReducer = combineReducers({
  [baseApi.reducerPath]: baseApi.reducer,
  auth: authReducer,
});
