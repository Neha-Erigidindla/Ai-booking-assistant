import streamlit as st
import pandas as pd
from datetime import datetime
from db.database import BookingDatabase


def show_admin_dashboard():
    """Display the admin dashboard with all bookings"""
    st.title("📊 Admin Dashboard")
    st.markdown("### Manage All Bookings")
    
    # Initialize database
    db = BookingDatabase()
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 All Bookings", "🔍 Search", "📈 Statistics"])
    
    with tab1:
        show_all_bookings(db)
    
    with tab2:
        show_search_bookings(db)
    
    with tab3:
        show_statistics(db)


def show_all_bookings(db):
    """Display all bookings in a table"""
    try:
        # Fetch all bookings
        bookings = db.get_all_bookings()
        
        if not bookings:
            st.info("📭 No bookings found yet.")
            return
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(bookings)
        
        # Display total count
        st.metric("Total Bookings", len(bookings))
        
        # Add filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All"] + list(df['status'].unique()),
                key="status_filter"
            )
        
        with col2:
            booking_type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + list(df['booking_type'].unique()),
                key="type_filter"
            )
        
        with col3:
            date_filter = st.selectbox(
                "Filter by Date",
                ["All"] + sorted(df['date'].unique(), reverse=True),
                key="date_filter"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if booking_type_filter != "All":
            filtered_df = filtered_df[filtered_df['booking_type'] == booking_type_filter]
        
        if date_filter != "All":
            filtered_df = filtered_df[filtered_df['date'] == date_filter]
        
        # Display filtered results
        st.markdown(f"**Showing {len(filtered_df)} of {len(bookings)} bookings**")
        
        # Display bookings as cards
        for idx, booking in filtered_df.iterrows():
            with st.expander(
                f"🎫 Booking #{booking['id']} - {booking['name']} - {booking['date']} at {booking['time']}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**📝 Booking ID:** {booking['id']}")
                    st.markdown(f"**👤 Name:** {booking['name']}")
                    st.markdown(f"**📧 Email:** {booking['email']}")
                    st.markdown(f"**📱 Phone:** {booking['phone']}")
                
                with col2:
                    st.markdown(f"**🎯 Service:** {booking['booking_type']}")
                    st.markdown(f"**📅 Date:** {booking['date']}")
                    st.markdown(f"**⏰ Time:** {booking['time']}")
                    st.markdown(f"**✅ Status:** {booking['status'].upper()}")
                
                st.markdown(f"**🕐 Created:** {booking['created_at']}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(
                        "✅ Confirm",
                        key=f"confirm_{booking['id']}",
                        disabled=(booking['status'] == 'confirmed')
                    ):
                        if db.update_booking_status(booking['id'], 'confirmed'):
                            st.success("Booking confirmed!")
                            st.rerun()
                
                with col2:
                    if st.button(
                        "❌ Cancel",
                        key=f"cancel_{booking['id']}",
                        disabled=(booking['status'] == 'cancelled')
                    ):
                        if db.update_booking_status(booking['id'], 'cancelled'):
                            st.warning("Booking cancelled!")
                            st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{booking['id']}"):
                        if db.delete_booking(booking['id']):
                            st.error("Booking deleted!")
                            st.rerun()
        
        # Export option
        st.markdown("---")
        if st.button("📥 Export to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"bookings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading bookings: {str(e)}")


def show_search_bookings(db):
    """Search bookings interface"""
    st.markdown("### 🔍 Search Bookings")
    
    search_term = st.text_input(
        "Search by name, email, or date",
        placeholder="Enter search term...",
        key="search_input"
    )
    
    if search_term:
        try:
            results = db.search_bookings(search_term)
            
            if not results:
                st.warning(f"No bookings found matching '{search_term}'")
                return
            
            st.success(f"Found {len(results)} booking(s)")
            
            # Display results
            for booking in results:
                with st.container():
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**Booking #{booking['id']}**")
                        st.markdown(f"👤 {booking['name']}")
                        st.markdown(f"📧 {booking['email']}")
                    
                    with col2:
                        st.markdown(f"**Service**")
                        st.markdown(f"🎯 {booking['booking_type']}")
                        st.markdown(f"📱 {booking['phone']}")
                    
                    with col3:
                        st.markdown(f"**Schedule**")
                        st.markdown(f"📅 {booking['date']}")
                        st.markdown(f"⏰ {booking['time']}")
                        st.markdown(f"✅ {booking['status'].upper()}")
        
        except Exception as e:
            st.error(f"Search error: {str(e)}")
    else:
        st.info("👆 Enter a search term to find bookings")


def show_statistics(db):
    """Show booking statistics"""
    st.markdown("### 📈 Booking Statistics")
    
    try:
        bookings = db.get_all_bookings()
        
        if not bookings:
            st.info("No data available for statistics")
            return
        
        df = pd.DataFrame(bookings)
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Bookings", len(df))
        
        with col2:
            confirmed = len(df[df['status'] == 'confirmed'])
            st.metric("Confirmed", confirmed)
        
        with col3:
            cancelled = len(df[df['status'] == 'cancelled'])
            st.metric("Cancelled", cancelled)
        
        with col4:
            unique_customers = df['email'].nunique()
            st.metric("Unique Customers", unique_customers)
        
        st.markdown("---")
        
        # Bookings by type
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Bookings by Service Type")
            type_counts = df['booking_type'].value_counts()
            st.bar_chart(type_counts)
        
        with col2:
            st.markdown("#### Bookings by Status")
            status_counts = df['status'].value_counts()
            st.bar_chart(status_counts)
        
        # Recent bookings
        st.markdown("---")
        st.markdown("#### 📅 Recent Bookings (Last 5)")
        recent = df.head(5)[['id', 'name', 'booking_type', 'date', 'time', 'status']]
        st.dataframe(recent, use_container_width=True, hide_index=True)
        
        # Upcoming bookings
        st.markdown("---")
        st.markdown("#### 🔜 Upcoming Bookings")
        
        today = datetime.now().strftime('%Y-%m-%d')
        upcoming = df[df['date'] >= today].sort_values('date')
        
        if len(upcoming) > 0:
            upcoming_display = upcoming[['id', 'name', 'booking_type', 'date', 'time']]
            st.dataframe(upcoming_display, use_container_width=True, hide_index=True)
        else:
            st.info("No upcoming bookings")
    
    except Exception as e:
        st.error(f"Error generating statistics: {str(e)}")