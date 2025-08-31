                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.content_optimization_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, content_optimization_enabled: e.target.checked}))}
                        className="w-4 h-4 text-gray-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <label className="font-medium text-gray-900">Suivi mots-clés</label>
                        <p className="text-sm text-gray-600">Analyse positions mots-clés</p>
                      </div>
                      <input
                        type="checkbox"
                        checked={storeConfigForm.keyword_tracking_enabled}
                        onChange={(e) => setStoreConfigForm(prev => ({...prev, keyword_tracking_enabled: e.target.checked}))}
                        className="w-4 h-4 text-gray-600 bg-gray-100 border-gray-300 rounded"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col md:flex-row justify-between pt-4 border-t space-y-2 md:space-y-0 md:space-x-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowStoreConfigModal(false);
                      setSelectedStoreForConfig(null);
                    }}
                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400 order-2 md:order-1 text-sm md:text-base"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    disabled={storeConfigLoading}
                    className="bg-purple-600 text-white px-4 md:px-6 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed order-1 md:order-2 text-sm md:text-base"
                  >
                    {storeConfigLoading ? '⏳ Enregistrement...' : '💾 Enregistrer Configuration'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
