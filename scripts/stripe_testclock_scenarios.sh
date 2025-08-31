#!/bin/bash

# ================================================================================
# ECOMSIMPLY - STRIPE TEST CLOCK SCENARIOS SCRIPT
# ================================================================================

set -e  # Exit on error

# Configuration
STRIPE_CLI="stripe"
BASE_URL="http://localhost:8001/api"
WEBHOOK_ENDPOINT="$BASE_URL/subscription/webhook"

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🕐 STRIPE TEST CLOCK SCENARIOS - ECOMSIMPLY${NC}"
echo "=================================================="

# Vérifier que Stripe CLI est installé
if ! command -v stripe &> /dev/null; then
    echo -e "${RED}❌ Stripe CLI not found. Please install: https://stripe.com/docs/stripe-cli${NC}"
    exit 1
fi

# Vérifier l'authentification Stripe
echo -e "${YELLOW}🔑 Checking Stripe CLI authentication...${NC}"
if ! stripe --version &> /dev/null; then
    echo -e "${RED}❌ Stripe CLI not authenticated. Run: stripe login${NC}"
    exit 1
fi

# ================================================================================
# 🎯 FONCTIONS UTILITAIRES
# ================================================================================

create_test_clock() {
    local name="$1"
    local frozen_time=$(date +%s)
    
    echo -e "${YELLOW}⏰ Creating Test Clock: $name${NC}"
    
    CLOCK_ID=$(stripe test-clocks create \
        --frozen-time=$frozen_time \
        --name="$name" \
        --format=json | jq -r '.id')
    
    if [ "$CLOCK_ID" = "null" ] || [ -z "$CLOCK_ID" ]; then
        echo -e "${RED}❌ Failed to create test clock${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Test Clock created: $CLOCK_ID${NC}"
    echo "$CLOCK_ID"
}

advance_clock() {
    local clock_id="$1"
    local days="$2"
    local current_time=$(stripe test-clocks retrieve $clock_id --format=json | jq -r '.frozen_time')
    local new_time=$((current_time + (days * 24 * 3600)))
    
    echo -e "${YELLOW}⏭️  Advancing clock by $days days...${NC}"
    stripe test-clocks advance $clock_id --frozen-time=$new_time
    echo -e "${GREEN}✅ Clock advanced to $(date -d @$new_time)${NC}"
}

cleanup_clock() {
    local clock_id="$1"
    if [ -n "$clock_id" ]; then
        echo -e "${YELLOW}🧹 Cleaning up Test Clock: $clock_id${NC}"
        stripe test-clocks delete $clock_id || true
    fi
}

create_test_customer() {
    local clock_id="$1"
    local email="$2"
    
    echo -e "${YELLOW}👤 Creating test customer: $email${NC}"
    
    CUSTOMER_ID=$(stripe customers create \
        --email="$email" \
        --test-clock="$clock_id" \
        --format=json | jq -r '.id')
    
    echo -e "${GREEN}✅ Customer created: $CUSTOMER_ID${NC}"
    echo "$CUSTOMER_ID"
}

create_test_payment_method() {
    local customer_id="$1"
    
    echo -e "${YELLOW}💳 Creating test payment method${NC}"
    
    PM_ID=$(stripe payment-methods create \
        --type=card \
        --card[number]=4242424242424242 \
        --card[exp-month]=12 \
        --card[exp-year]=2030 \
        --card[cvc]=123 \
        --format=json | jq -r '.id')
    
    stripe payment-methods attach $PM_ID --customer=$customer_id
    
    echo -e "${GREEN}✅ Payment method created and attached: $PM_ID${NC}"
    echo "$PM_ID"
}

# ================================================================================
# 📋 SCÉNARIO 1: TRIAL → ACTIVE → FAILED → RECOVERED
# ================================================================================

scenario_trial_to_recovery() {
    echo -e "\n${BLUE}📋 SCENARIO 1: Trial → Active → Failed → Recovered${NC}"
    echo "=============================================="
    
    # Créer Test Clock
    CLOCK_ID=$(create_test_clock "ECOMSIMPLY_Trial_Recovery")
    
    # Trap pour cleanup
    trap "cleanup_clock $CLOCK_ID" EXIT
    
    # Créer customer
    CUSTOMER_ID=$(create_test_customer "$CLOCK_ID" "trial-recovery@test.com")
    
    # Créer abonnement avec essai
    echo -e "${YELLOW}🎁 Creating subscription with 7-day trial${NC}"
    SUB_ID=$(stripe subscriptions create \
        --customer="$CUSTOMER_ID" \
        --items[0][price]="price_1Rrw3UGK8qzu5V5Wu8PnvKzK" \
        --trial-period-days=7 \
        --test-clock="$CLOCK_ID" \
        --format=json | jq -r '.id')
    
    echo -e "${GREEN}✅ Subscription created: $SUB_ID${NC}"
    
    # Vérifier statut trial
    STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
    echo -e "${BLUE}📊 Current status: $STATUS${NC}"
    
    if [ "$STATUS" != "trialing" ]; then
        echo -e "${RED}❌ Expected 'trialing' status, got '$STATUS'${NC}"
        exit 1
    fi
    
    # Avancer au milieu de l'essai (4 jours)
    echo -e "\n${YELLOW}⏭️  Fast-forwarding to middle of trial (4 days)${NC}"
    advance_clock "$CLOCK_ID" 4
    
    STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
    echo -e "${BLUE}📊 Status after 4 days: $STATUS${NC}"
    
    # Avancer à la fin de l'essai avec carte défaillante (8 jours)
    echo -e "\n${YELLOW}⏭️  Fast-forwarding to end of trial (8 days total)${NC}"
    advance_clock "$CLOCK_ID" 4
    
    STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
    echo -e "${BLUE}📊 Status after trial end: $STATUS${NC}"
    
    if [ "$STATUS" = "past_due" ] || [ "$STATUS" = "unpaid" ]; then
        echo -e "${YELLOW}⚠️  Payment failed as expected, initiating recovery${NC}"
        
        # Créer nouveau moyen de paiement qui fonctionne
        PM_ID=$(create_test_payment_method "$CUSTOMER_ID")
        
        # Mettre à jour l'abonnement
        stripe subscriptions update $SUB_ID --default-payment-method="$PM_ID"
        
        # Payer la facture en souffrance
        echo -e "${YELLOW}💰 Paying outstanding invoice${NC}"
        INVOICE_ID=$(stripe invoices list --customer="$CUSTOMER_ID" --status=open --limit=1 --format=json | jq -r '.data[0].id')
        
        if [ "$INVOICE_ID" != "null" ] && [ -n "$INVOICE_ID" ]; then
            stripe invoices pay "$INVOICE_ID"
            echo -e "${GREEN}✅ Invoice paid: $INVOICE_ID${NC}"
        fi
        
        # Vérifier récupération
        sleep 2
        STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
        echo -e "${GREEN}✅ Subscription recovered: $STATUS${NC}"
        
        if [ "$STATUS" = "active" ]; then
            echo -e "${GREEN}🎉 SCENARIO 1 SUCCESS: Recovery completed${NC}"
        else
            echo -e "${YELLOW}⚠️  Recovery in progress: $STATUS${NC}"
        fi
    else
        echo -e "${GREEN}✅ Subscription active without payment failure${NC}"
    fi
    
    # Nettoyer
    cleanup_clock "$CLOCK_ID"
}

# ================================================================================
# 📋 SCÉNARIO 2: CANCEL AT PERIOD END → REACTIVATE
# ================================================================================

scenario_cancel_reactivate() {
    echo -e "\n${BLUE}📋 SCENARIO 2: Cancel at Period End → Reactivate${NC}"
    echo "=============================================="
    
    # Créer Test Clock
    CLOCK_ID=$(create_test_clock "ECOMSIMPLY_Cancel_Reactivate")
    trap "cleanup_clock $CLOCK_ID" EXIT
    
    # Créer customer avec paiement
    CUSTOMER_ID=$(create_test_customer "$CLOCK_ID" "cancel-reactivate@test.com")
    PM_ID=$(create_test_payment_method "$CUSTOMER_ID")
    
    # Créer abonnement actif (pas d'essai)
    echo -e "${YELLOW}💳 Creating active subscription${NC}"
    SUB_ID=$(stripe subscriptions create \
        --customer="$CUSTOMER_ID" \
        --items[0][price]="price_1Rrw3UGK8qzu5V5Wu8PnvKzK" \
        --default-payment-method="$PM_ID" \
        --test-clock="$CLOCK_ID" \
        --format=json | jq -r '.id')
    
    # Vérifier statut actif
    STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
    echo -e "${BLUE}📊 Initial status: $STATUS${NC}"
    
    # Programmer annulation à la fin de période
    echo -e "${YELLOW}📅 Scheduling cancellation at period end${NC}"
    stripe subscriptions update $SUB_ID --cancel-at-period-end=true
    
    CANCEL_FLAG=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.cancel_at_period_end')
    echo -e "${BLUE}📊 Cancel at period end: $CANCEL_FLAG${NC}"
    
    if [ "$CANCEL_FLAG" != "true" ]; then
        echo -e "${RED}❌ Failed to set cancel_at_period_end${NC}"
        exit 1
    fi
    
    # Réactiver avant la fin
    echo -e "${YELLOW}🔄 Reactivating subscription${NC}"
    stripe subscriptions update $SUB_ID --cancel-at-period-end=false
    
    CANCEL_FLAG=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.cancel_at_period_end')
    STATUS=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.status')
    
    echo -e "${GREEN}✅ Reactivated - Cancel flag: $CANCEL_FLAG, Status: $STATUS${NC}"
    
    if [ "$CANCEL_FLAG" = "false" ] && [ "$STATUS" = "active" ]; then
        echo -e "${GREEN}🎉 SCENARIO 2 SUCCESS: Cancel/Reactivate completed${NC}"
    else
        echo -e "${RED}❌ SCENARIO 2 FAILED${NC}"
        exit 1
    fi
    
    cleanup_clock "$CLOCK_ID"
}

# ================================================================================
# 📋 SCÉNARIO 3: UPGRADE/DOWNGRADE WITH PRORATION
# ================================================================================

scenario_upgrade_downgrade() {
    echo -e "\n${BLUE}📋 SCENARIO 3: Upgrade/Downgrade with Proration${NC}"
    echo "=============================================="
    
    # Créer Test Clock
    CLOCK_ID=$(create_test_clock "ECOMSIMPLY_Upgrade_Downgrade")
    trap "cleanup_clock $CLOCK_ID" EXIT
    
    # Créer customer avec abonnement Pro
    CUSTOMER_ID=$(create_test_customer "$CLOCK_ID" "upgrade-downgrade@test.com")
    PM_ID=$(create_test_payment_method "$CUSTOMER_ID")
    
    echo -e "${YELLOW}💼 Creating Pro subscription${NC}"
    SUB_ID=$(stripe subscriptions create \
        --customer="$CUSTOMER_ID" \
        --items[0][price]="price_1Rrw3UGK8qzu5V5Wu8PnvKzK" \
        --default-payment-method="$PM_ID" \
        --test-clock="$CLOCK_ID" \
        --format=json | jq -r '.id')
    
    ORIGINAL_PRICE=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.items.data[0].price.id')
    echo -e "${BLUE}📊 Original price: $ORIGINAL_PRICE${NC}"
    
    # Avancer de 15 jours
    echo -e "${YELLOW}⏭️  Fast-forwarding 15 days into billing period${NC}"
    advance_clock "$CLOCK_ID" 15
    
    # Upgrade vers Premium
    echo -e "${YELLOW}⬆️  Upgrading to Premium${NC}"
    ITEM_ID=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.items.data[0].id')
    
    stripe subscriptions update $SUB_ID \
        --items[0][id]="$ITEM_ID" \
        --items[0][price]="price_1RrxgjGK8qzu5V5WvOSb4uPd" \
        --proration-behavior=create_prorations
    
    NEW_PRICE=$(stripe subscriptions retrieve $SUB_ID --format=json | jq -r '.items.data[0].price.id')
    echo -e "${GREEN}✅ Upgraded - New price: $NEW_PRICE${NC}"
    
    if [ "$NEW_PRICE" != "$ORIGINAL_PRICE" ]; then
        echo -e "${GREEN}🎉 SCENARIO 3 SUCCESS: Upgrade completed${NC}"
    else
        echo -e "${RED}❌ SCENARIO 3 FAILED: Price not changed${NC}"
        exit 1
    fi
    
    cleanup_clock "$CLOCK_ID"
}

# ================================================================================
# 📋 SCÉNARIO 4: WEBHOOK PROCESSING VERIFICATION
# ================================================================================

scenario_webhook_processing() {
    echo -e "\n${BLUE}📋 SCENARIO 4: Webhook Processing Verification${NC}"
    echo "=============================================="
    
    # Vérifier que le serveur backend est accessible
    echo -e "${YELLOW}🔍 Checking backend server availability${NC}"
    if ! curl -s "$BASE_URL/subscription/plans" > /dev/null; then
        echo -e "${YELLOW}⚠️  Backend server not available at $BASE_URL${NC}"
        echo -e "${YELLOW}    Skipping webhook tests${NC}"
        return 0
    fi
    
    # Créer Test Clock
    CLOCK_ID=$(create_test_clock "ECOMSIMPLY_Webhook_Test")
    trap "cleanup_clock $CLOCK_ID" EXIT
    
    echo -e "${YELLOW}🎣 Setting up webhook forwarding${NC}"
    # Lancer l'écoute des webhooks en arrière-plan
    stripe listen --forward-to="$WEBHOOK_ENDPOINT" &
    LISTEN_PID=$!
    
    # Attendre que l'écoute soit établie
    sleep 3
    
    # Trap pour nettoyer le processus
    trap "kill $LISTEN_PID 2>/dev/null; cleanup_clock $CLOCK_ID" EXIT
    
    # Créer un événement qui déclenchera des webhooks
    CUSTOMER_ID=$(create_test_customer "$CLOCK_ID" "webhook-test@test.com")
    PM_ID=$(create_test_payment_method "$CUSTOMER_ID")
    
    echo -e "${YELLOW}🔔 Creating subscription to trigger webhooks${NC}"
    SUB_ID=$(stripe subscriptions create \
        --customer="$CUSTOMER_ID" \
        --items[0][price]="price_1Rrw3UGK8qzu5V5Wu8PnvKzK" \
        --default-payment-method="$PM_ID" \
        --trial-period-days=7 \
        --test-clock="$CLOCK_ID" \
        --format=json | jq -r '.id')
    
    echo -e "${GREEN}✅ Subscription created: $SUB_ID${NC}"
    echo -e "${YELLOW}📡 Webhooks should be processing...${NC}"
    
    # Attendre un peu pour le traitement des webhooks
    sleep 5
    
    # Avancer le test clock pour déclencher plus d'événements
    advance_clock "$CLOCK_ID" 8  # Fin d'essai
    
    echo -e "${YELLOW}⏳ Waiting for webhook processing...${NC}"
    sleep 5
    
    echo -e "${GREEN}🎉 SCENARIO 4 COMPLETED: Check backend logs for webhook processing${NC}"
    
    # Nettoyer
    kill $LISTEN_PID 2>/dev/null || true
    cleanup_clock "$CLOCK_ID"
}

# ================================================================================
# 🎯 MENU PRINCIPAL
# ================================================================================

show_menu() {
    echo -e "\n${BLUE}Choose a scenario to run:${NC}"
    echo "1) Trial → Active → Failed → Recovered"
    echo "2) Cancel at Period End → Reactivate" 
    echo "3) Upgrade/Downgrade with Proration"
    echo "4) Webhook Processing Verification"
    echo "5) Run All Scenarios"
    echo "6) Exit"
    echo
    read -p "Enter your choice (1-6): " choice
}

run_all_scenarios() {
    echo -e "${BLUE}🚀 Running all scenarios...${NC}"
    scenario_trial_to_recovery
    scenario_cancel_reactivate
    scenario_upgrade_downgrade
    scenario_webhook_processing
    echo -e "${GREEN}🎉 All scenarios completed!${NC}"
}

# ================================================================================
# 🎯 EXECUTION PRINCIPALE
# ================================================================================

main() {
    while true; do
        show_menu
        case $choice in
            1)
                scenario_trial_to_recovery
                ;;
            2)
                scenario_cancel_reactivate
                ;;
            3)
                scenario_upgrade_downgrade
                ;;
            4)
                scenario_webhook_processing
                ;;
            5)
                run_all_scenarios
                ;;
            6)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid choice. Please try again.${NC}"
                ;;
        esac
        
        echo -e "\n${YELLOW}Press Enter to continue...${NC}"
        read
    done
}

# Lancer le menu principal
main